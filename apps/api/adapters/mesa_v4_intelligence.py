import asyncio
import logging
from typing import Any, TypeVar

import httpx
from apps.api.core.config import settings
from apps.api.core.ports.ingestion import IngestionItem, MesaIngestionPort
from apps.api.core.ports.intelligence import (
    Evidence,
    IntelligenceQuery,
    IntelligenceResponse,
    MesaIntelligencePort,
    OperationState,
)
from apps.api.core.ports.mesa_v4 import (
    AdmissionResponse,
    CapabilityResponse,
    DatasetRequest,
    DocumentRequest,
    MemoryInsertRequest,
    MesaAuthenticationError,
    MesaCapacityError,
    MesaConflictError,
    MesaContractError,
    MesaUnavailableError,
    MesaV4Error,
    MutationStatusResponse,
    RevisionRequest,
    SearchRequest,
    SearchResponse,
    SessionResponse,
    SessionStartRequest,
    SourceChunkRequest,
    WorkspaceRequest,
)
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)

MESA_CORE_COMMIT = "c5901881fc414dfd3475c386d2c59bb461e65cd2"
MESA_CORE_VERSION = "0.7.1"


class MesaV4HttpAdapter(MesaIntelligencePort, MesaIngestionPort):
    """Typed HTTP boundary for the pinned MESA Core v4 contract."""

    def __init__(
        self,
        backend_url: str = settings.mesa_backend_url,
        api_key: str = settings.mesa_api_key,
        *,
        timeout_seconds: float = 10.0,
        max_attempts: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.max_attempts = max(1, max_attempts)
        self.client = client or httpx.AsyncClient(
            base_url=self.backend_url,
            headers={"Content-Type": "application/json", "X-API-Key": api_key},
            timeout=timeout_seconds,
        )
        self._owns_client = client is None

    @staticmethod
    def _detail(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text[:500]
        if isinstance(body, dict):
            detail = body.get("detail") or body.get("error")
            if detail is not None:
                return str(detail)[:500]
        return str(body)[:500]

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response: httpx.Response | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self.client.request(
                    method, path, json=json, params=params
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == self.max_attempts:
                    raise MesaUnavailableError(
                        "MESA Core is unavailable",
                        detail=type(exc).__name__,
                        retryable=True,
                    ) from exc
                await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
                continue

            if response.status_code in {502, 503, 504} and attempt < self.max_attempts:
                await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
                continue
            break

        if response is None:  # pragma: no cover - loop always sets or raises
            raise MesaUnavailableError("MESA Core request did not execute")

        detail = self._detail(response)
        if response.status_code in {401, 403}:
            raise MesaAuthenticationError(
                "MESA Core authentication or authorization failed",
                status_code=response.status_code,
                detail=detail,
            )
        if response.status_code == 409:
            raise MesaConflictError(
                "MESA Core rejected a conflicting request",
                status_code=409,
                detail=detail,
                retryable="in progress" in detail.lower(),
            )
        if response.status_code == 413:
            raise MesaCapacityError(
                "MESA Core rejected an oversized queue record",
                status_code=413,
                detail=detail,
            )
        if response.status_code in {429, 502, 503, 504}:
            raise MesaUnavailableError(
                "MESA Core is temporarily unavailable",
                status_code=response.status_code,
                detail=detail,
                retryable=True,
            )
        if response.status_code >= 400:
            raise MesaContractError(
                "MESA Core returned an unexpected response",
                status_code=response.status_code,
                detail=detail,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise MesaContractError(
                "MESA Core returned non-JSON data",
                status_code=response.status_code,
            ) from exc
        if not isinstance(data, dict):
            raise MesaContractError("MESA Core response must be a JSON object")
        return data

    @staticmethod
    def _parse(model: type[ResponseModel], data: dict[str, Any]) -> ResponseModel:
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise MesaContractError(
                f"MESA Core response violated {model.__name__}"
            ) from exc

    async def capability(self) -> CapabilityResponse:
        data = await self._request("GET", "/v4/capability")
        return self._parse(CapabilityResponse, data)

    async def create_workspace(self, request: WorkspaceRequest) -> dict[str, Any]:
        return await self._request(
            "POST", "/v4/catalog/workspaces", json=request.model_dump(exclude_none=True)
        )

    async def list_workspaces(self, tenant_id: str) -> list[dict[str, Any]]:
        data = await self._request(
            "GET", "/v4/catalog/workspaces", params={"tenant_id": tenant_id}
        )
        workspaces = data.get("workspaces")
        if not isinstance(workspaces, list):
            raise MesaContractError("MESA workspace list is malformed")
        return workspaces

    async def create_dataset(self, request: DatasetRequest) -> dict[str, Any]:
        return await self._request(
            "POST", "/v4/catalog/datasets", json=request.model_dump(exclude_none=True)
        )

    async def list_datasets(
        self, tenant_id: str, workspace_id: str
    ) -> list[dict[str, Any]]:
        data = await self._request(
            "GET",
            "/v4/catalog/datasets",
            params={"tenant_id": tenant_id, "workspace_id": workspace_id},
        )
        datasets = data.get("datasets")
        if not isinstance(datasets, list):
            raise MesaContractError("MESA dataset list is malformed")
        return datasets

    async def preflight_scope(
        self, *, tenant_id: str, workspace_id: str, dataset_id: str
    ) -> None:
        capability = await self.capability()
        if capability.api_version != "v4":
            raise MesaContractError("MESA Core does not report the v4 capability")
        workspaces = await self.list_workspaces(tenant_id)
        if not any(item.get("workspace_id") == workspace_id for item in workspaces):
            raise MesaAuthenticationError("Provisioned MESA workspace is not visible")
        datasets = await self.list_datasets(tenant_id, workspace_id)
        if not any(item.get("dataset_id") == dataset_id for item in datasets):
            raise MesaAuthenticationError("Provisioned MESA dataset is not visible")

    async def create_document(self, request: DocumentRequest) -> dict[str, Any]:
        return await self._request(
            "POST", "/v4/catalog/documents", json=request.model_dump(exclude_none=True)
        )

    async def create_revision(self, request: RevisionRequest) -> dict[str, Any]:
        return await self._request(
            "POST", "/v4/catalog/revisions", json=request.model_dump(exclude_none=True)
        )

    async def create_source_chunk(self, request: SourceChunkRequest) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/v4/catalog/source-chunks",
            json=request.model_dump(exclude_none=True),
        )

    async def start_session(self, request: SessionStartRequest) -> SessionResponse:
        data = await self._request(
            "POST", "/v4/sessions/start", json=request.model_dump()
        )
        data.pop("status", None)
        data["status"] = "ACTIVE"
        return self._parse(SessionResponse, data)

    async def session_context(self, session_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v4/sessions/{session_id}/context")

    async def end_session(self, session_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/v4/sessions/{session_id}/end")

    async def insert_memory(self, request: MemoryInsertRequest) -> AdmissionResponse:
        if not request.idempotency_key:
            raise MesaContractError("MESA v4 inserts require an idempotency key")
        data = await self._request(
            "POST", "/v4/memory/insert", json=request.model_dump(exclude_none=True)
        )
        return self._parse(AdmissionResponse, data)

    async def search_memory(self, request: SearchRequest) -> SearchResponse:
        data = await self._request(
            "POST",
            "/v4/memory/search",
            json=request.model_dump(exclude_none=True, mode="json"),
        )
        return self._parse(SearchResponse, data)

    async def mutation_status(self, mutation_id: str) -> MutationStatusResponse:
        data = await self._request("GET", f"/v4/mutations/{mutation_id}")
        return self._parse(MutationStatusResponse, data)

    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        if not query.session_id or not query.dataset_ids:
            return IntelligenceResponse(
                state=OperationState.unavailable,
                error_message="A provisioned MESA v4 session and dataset scope are required.",
            )
        try:
            response = await self.search_memory(
                SearchRequest(
                    session_id=query.session_id,
                    dataset_ids=query.dataset_ids,
                    query=query.query_text,
                )
            )
        except MesaV4Error as exc:
            logger.warning("MESA v4 search unavailable: %s", exc)
            return IntelligenceResponse(
                state=OperationState.unavailable,
                error_message=str(exc),
            )

        evidence: list[Evidence] = []
        for result in response.results:
            for provenance in result.provenance:
                metadata = provenance.metadata
                page_number = metadata.get("page_number")
                evidence_text = metadata.get("evidence_text")
                evidence.append(
                    Evidence(
                        dataset_id=provenance.dataset_id,
                        document_id=provenance.document_id,
                        revision_id=provenance.revision_id,
                        chunk_id=provenance.chunk_id,
                        source_ref=provenance.source_ref,
                        evidence_span=provenance.evidence_span,
                        page_number=page_number
                        if isinstance(page_number, int)
                        else None,
                        text_snippet=evidence_text
                        if isinstance(evidence_text, str)
                        else "",
                        metadata=metadata,
                        score=result.final_score,
                    )
                )
        if not evidence:
            return IntelligenceResponse(state=OperationState.no_evidence_retrieved)
        return IntelligenceResponse(
            state=OperationState.success,
            evidence=evidence,
            summary=f"MESA Core returned {len(response.results)} candidate result(s).",
        )

    async def ingest(self, item: IngestionItem) -> bool:
        if not all((item.session_id, item.dataset_id, item.chunk_id, item.source_ref)):
            raise MesaContractError("Legacy ingestion item lacks MESA v4 scope")
        assert item.session_id is not None
        assert item.dataset_id is not None
        assert item.chunk_id is not None
        assert item.source_ref is not None
        await self.insert_memory(
            MemoryInsertRequest(
                session_id=item.session_id,
                dataset_id=item.dataset_id,
                document_id=item.document_id,
                revision_id=item.revision_id,
                chunk_id=item.chunk_id,
                title=item.source_name,
                source_ref=item.source_ref,
                content=item.text_content,
                evidence_span=item.evidence_span,
                chunk_ordinal=item.chunk_ordinal,
                metadata=item.metadata,
                idempotency_key=item.idempotency_key,
            )
        )
        return True

    async def rebuild_tenant(self, tenant_id: str) -> bool:
        raise MesaContractError(
            "MESA Core v4 rebuild is not implemented", status_code=501
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
