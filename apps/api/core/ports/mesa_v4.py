from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictMesaModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class WorkspaceRequest(StrictMesaModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=128)
    tenant_name: str | None = Field(default=None, max_length=256)
    workspace_name: str | None = Field(default=None, max_length=256)


class DatasetRequest(WorkspaceRequest):
    dataset_id: str = Field(min_length=1, max_length=128)
    dataset_name: str | None = Field(default=None, max_length=256)


class DocumentRequest(StrictMesaModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=128)
    dataset_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=512)
    external_ref: str | None = Field(default=None, max_length=2048)


class RevisionRequest(StrictMesaModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=128)
    dataset_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=256)
    revision_id: str = Field(min_length=1, max_length=256)
    revision_number: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    supersedes_revision_id: str | None = Field(default=None, max_length=256)


class SourceChunkRequest(StrictMesaModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=128)
    dataset_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=256)
    revision_id: str = Field(min_length=1, max_length=256)
    chunk_id: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1, max_length=32768)
    source_ref: str = Field(min_length=1, max_length=2048)
    revision_number: int = Field(default=1, ge=1)
    chunk_ordinal: int = Field(default=0, ge=0)
    external_ref: str | None = Field(default=None, max_length=2048)
    supersedes_revision_id: str | None = Field(default=None, max_length=256)


class SessionStartRequest(StrictMesaModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=128)
    dataset_ids: list[str] = Field(min_length=1, max_length=64)
    agent_id: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    session_id: str
    tenant_id: str
    workspace_id: str
    dataset_ids: list[str]
    agent_id: str
    status: str


class MemoryInsertRequest(StrictMesaModel):
    session_id: str = Field(min_length=1, max_length=128)
    dataset_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=256)
    revision_id: str = Field(min_length=1, max_length=256)
    chunk_id: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=512)
    source_ref: str = Field(min_length=1, max_length=2048)
    content: str = Field(min_length=1, max_length=32768)
    evidence_span: str = Field(default="", max_length=4096)
    revision_number: int = Field(default=1, ge=1)
    chunk_ordinal: int = Field(default=0, ge=0)
    supersedes_revision_id: str | None = Field(default=None, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)


class AdmissionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    mutation_id: str
    candidate_id: str
    pipeline_run_id: str
    raw_log_id: int
    duplicate: bool = False


class SearchRequest(StrictMesaModel):
    session_id: str = Field(min_length=1, max_length=128)
    dataset_ids: list[str] | None = Field(default=None, max_length=64)
    query: str = Field(min_length=1, max_length=4096)
    limit: int = Field(default=10, ge=1, le=50)
    jurisdiction: str | None = Field(default=None, max_length=256)
    valid_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    dataset_id: str
    document_id: str
    revision_id: str
    chunk_id: str
    source_ref: str
    evidence_span: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity: dict[str, Any]
    rrf_score: float
    legal_factor: float
    final_score: float
    provenance: list[ProvenanceRecord] = Field(default_factory=list)


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    dataset_ids: list[str]
    results: list[SearchResult]


class MutationState(StrEnum):
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"
    DEAD_LETTER = "DEAD_LETTER"
    ROLLED_BACK = "ROLLED_BACK"
    BLOCKED = "BLOCKED"


TERMINAL_MUTATION_STATES = frozenset(MutationState)


class MutationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mutation_id: str
    candidate_id: str
    state: str
    failure_class: str | None = None
    rejection_reason: str | None = None
    tier3_audit: dict[str, Any] | None = None
    pipeline_run: dict[str, Any] | None = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    projections: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_MUTATION_STATES


class CapabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: list[str]
    api_version: str


class MesaV4Error(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        self.retryable = retryable


class MesaAuthenticationError(MesaV4Error):
    pass


class MesaConflictError(MesaV4Error):
    pass


class MesaCapacityError(MesaV4Error):
    pass


class MesaUnavailableError(MesaV4Error):
    pass


class MesaContractError(MesaV4Error):
    pass
