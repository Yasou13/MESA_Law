import hashlib
import logging

from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.core.ports.intelligence import IntelligenceQuery, OperationState
from apps.api.core.ports.mesa_v4 import MesaV4Error, SessionStartRequest
from apps.api.models.document import Document, DocumentRevision
from apps.api.models.domain import SourceLocator
from apps.api.models.mesa import MesaScopeBinding
from apps.api.models.parser import DocumentChunk, ParsedDocument, ParsedPage
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api.qa")


class QACitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    revision_id: str
    page_number: int | None
    low_provenance: bool
    provenance_state: str
    chunk_id: str
    text_start: int
    text_end: int
    evidence_excerpt: str
    evidence_sha256: str


class QAResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    status: str
    citations: list[QACitation] = Field(default_factory=list)
    degraded_reason: str | None = None


class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4096)


def _citation_from_local_chunk(
    chunk: DocumentChunk,
    page: ParsedPage,
    revision: DocumentRevision,
) -> QACitation | None:
    if (
        not revision.is_canonical
        or chunk.revision_id != revision.id
        or chunk.page_id != page.id
        or chunk.character_start is None
        or chunk.character_end is None
        or chunk.character_end > len(page.text_content)
    ):
        return None
    evidence = page.text_content[chunk.character_start : chunk.character_end]
    digest = hashlib.sha256(evidence.encode("utf-8")).hexdigest()
    if evidence != chunk.text_content or digest != chunk.content_sha256:
        return None
    low = chunk.provenance_state == "LOW_PROVENANCE"
    if not low and not chunk.provenance_state.startswith("VERIFIED_PDF"):
        return None
    return QACitation(
        document_id=chunk.document_id,
        revision_id=revision.id,
        page_number=None if low else page.page_number,
        low_provenance=low,
        provenance_state=chunk.provenance_state,
        chunk_id=chunk.id,
        text_start=chunk.character_start,
        text_end=chunk.character_end,
        evidence_excerpt=evidence[:500],
        evidence_sha256=digest,
    )


async def _lexical_citations(
    session: AsyncSession,
    *,
    tenant_id: str,
    matter_id: str,
    document_id: str | None,
    question: str,
    limit: int = 5,
) -> list[QACitation]:
    query_vector = func.plainto_tsquery("turkish", question)
    rank = func.ts_rank_cd(DocumentChunk.fts_vector, query_vector)
    statement = (
        select(DocumentChunk, ParsedPage, DocumentRevision)
        .join(ParsedPage, DocumentChunk.page_id == ParsedPage.id)
        .join(ParsedDocument, ParsedPage.parsed_document_id == ParsedDocument.id)
        .join(Document, DocumentChunk.document_id == Document.id)
        .join(DocumentRevision, DocumentChunk.revision_id == DocumentRevision.id)
        .where(
            DocumentChunk.tenant_id == tenant_id,
            Document.tenant_id == tenant_id,
            Document.matter_id == matter_id,
            DocumentRevision.is_canonical.is_(True),
            DocumentChunk.fts_vector.op("@@")(query_vector),
        )
        .order_by(rank.desc(), DocumentChunk.id)
        .limit(limit)
    )
    if document_id:
        statement = statement.where(Document.id == document_id)
    rows = (await session.execute(statement)).all()
    citations = []
    for chunk, page, revision in rows:
        citation = _citation_from_local_chunk(chunk, page, revision)
        if citation is not None:
            citations.append(citation)
    return citations


async def _verify_mesa_evidence(
    session: AsyncSession,
    *,
    tenant_id: str,
    matter_id: str,
    dataset_id: str,
    document_filter: str | None,
    evidence,
) -> QACitation | None:
    if evidence.dataset_id != dataset_id:
        return None
    if document_filter and evidence.document_id != document_filter:
        return None
    locator_id = evidence.metadata.get("source_locator_id")
    if not isinstance(locator_id, str):
        return None
    row = (
        await session.execute(
            select(
                SourceLocator,
                DocumentChunk,
                ParsedPage,
                DocumentRevision,
                Document,
            )
            .join(DocumentChunk, SourceLocator.chunk_id == DocumentChunk.id)
            .join(ParsedPage, SourceLocator.parsed_page_id == ParsedPage.id)
            .join(
                DocumentRevision,
                SourceLocator.document_revision_id == DocumentRevision.id,
            )
            .join(Document, SourceLocator.document_id == Document.id)
            .where(
                SourceLocator.id == locator_id,
                SourceLocator.tenant_id == tenant_id,
                SourceLocator.matter_id == matter_id,
                Document.matter_id == matter_id,
                Document.tenant_id == tenant_id,
            )
        )
    ).one_or_none()
    if row is None:
        return None
    locator, chunk, page, revision, _ = row
    if (
        evidence.document_id != locator.document_id
        or evidence.revision_id != locator.document_revision_id
        or evidence.chunk_id != locator.chunk_id
        or evidence.source_ref
        != f"mesa-law://{tenant_id}/{matter_id}/{locator.document_id}/"
        f"{locator.document_revision_id}/{locator.chunk_id}"
        or locator.character_start is None
        or locator.character_end is None
        or locator.evidence_text is None
        or locator.evidence_sha256 is None
    ):
        return None
    local_evidence = page.text_content[locator.character_start : locator.character_end]
    if (
        local_evidence != locator.evidence_text
        or evidence.evidence_span != local_evidence
        or evidence.metadata.get("evidence_sha256") != locator.evidence_sha256
        or hashlib.sha256(local_evidence.encode()).hexdigest()
        != locator.evidence_sha256
    ):
        return None
    base = _citation_from_local_chunk(chunk, page, revision)
    if base is None:
        return None
    return base.model_copy(
        update={
            "text_start": locator.character_start,
            "text_end": locator.character_end,
            "evidence_excerpt": local_evidence[:500],
            "evidence_sha256": locator.evidence_sha256,
        }
    )


async def _mesa_citations(
    session: AsyncSession,
    *,
    binding: MesaScopeBinding,
    tenant_id: str,
    matter_id: str,
    document_id: str | None,
    question: str,
) -> tuple[list[QACitation], str | None]:
    adapter = MesaV4HttpAdapter()
    mesa_session_id: str | None = None
    try:
        await adapter.preflight_scope(
            tenant_id=binding.mesa_tenant_id,
            workspace_id=binding.workspace_id,
            dataset_id=binding.dataset_id,
        )
        mesa_session = await adapter.start_session(
            SessionStartRequest(
                tenant_id=binding.mesa_tenant_id,
                workspace_id=binding.workspace_id,
                dataset_ids=[binding.dataset_id],
                agent_id=binding.agent_id,
            )
        )
        mesa_session_id = mesa_session.session_id
        response = await adapter.query(
            IntelligenceQuery(
                tenant_id=tenant_id,
                matter_id=matter_id,
                session_id=mesa_session.session_id,
                dataset_ids=[binding.dataset_id],
                query_text=question,
            )
        )
        if response.state == OperationState.no_evidence_retrieved:
            return [], None
        if response.state != OperationState.success:
            return [], response.error_message or f"MESA_{response.state.value.upper()}"
        citations = []
        for evidence in response.evidence:
            citation = await _verify_mesa_evidence(
                session,
                tenant_id=tenant_id,
                matter_id=matter_id,
                dataset_id=binding.dataset_id,
                document_filter=document_id,
                evidence=evidence,
            )
            if citation is not None:
                citations.append(citation)
            else:
                logger.warning("Rejected unverifiable MESA provenance")
        return citations, None if citations else "MESA_PROVENANCE_UNVERIFIED"
    except MesaV4Error as exc:
        return [], f"MESA_UNAVAILABLE:{type(exc).__name__}"
    finally:
        if mesa_session_id:
            try:
                await adapter.end_session(mesa_session_id)
            except MesaV4Error:
                logger.warning("Could not end the ephemeral MESA QA session")
        await adapter.close()


def _extractive_answer(question: str, citations: list[QACitation]) -> str:
    excerpts = "\n".join(f"- {citation.evidence_excerpt}" for citation in citations[:5])
    return f"“{question}” sorusu için doğrulanmış kaynak eşleşmeleri:\n{excerpts}"


async def ask_matter_question(
    session: AsyncSession,
    tenant_id: str,
    matter_id: str,
    document_id: str | None,
    question: str,
) -> QAResponse:
    binding = await session.scalar(
        select(MesaScopeBinding).where(
            MesaScopeBinding.tenant_id == tenant_id,
            MesaScopeBinding.matter_id == matter_id,
        )
    )
    degraded_reason: str | None = None
    citations: list[QACitation] = []
    if binding is not None and binding.provisioning_status == "READY":
        citations, degraded_reason = await _mesa_citations(
            session,
            binding=binding,
            tenant_id=tenant_id,
            matter_id=matter_id,
            document_id=document_id,
            question=question,
        )
        if citations:
            return QAResponse(
                answer=_extractive_answer(question, citations),
                status="ANSWERED",
                citations=citations,
            )
    else:
        degraded_reason = "MESA_SCOPE_NOT_READY"

    lexical = await _lexical_citations(
        session,
        tenant_id=tenant_id,
        matter_id=matter_id,
        document_id=document_id,
        question=question,
    )
    if lexical:
        return QAResponse(
            answer=_extractive_answer(question, lexical),
            status="DEGRADED",
            citations=lexical,
            degraded_reason=degraded_reason or "MESA_NO_VERIFIED_EVIDENCE",
        )
    return QAResponse(
        answer=(
            "Bu soruyu yanıtlamak için matter kapsamında yeterli doğrulanmış "
            "kaynak bulunamadı."
        ),
        status="ABSTAIN",
        citations=[],
        degraded_reason=degraded_reason or "NO_VERIFIED_EVIDENCE",
    )
