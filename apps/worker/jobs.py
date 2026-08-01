from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class JobPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tenant_id: str = Field(min_length=1)
    matter_id: str = Field(min_length=1)


class ScanDocumentPayload(JobPayload):
    type: Literal["SCAN_DOCUMENT"] = "SCAN_DOCUMENT"
    document_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    s3_key: str = Field(min_length=1)


class ParseDocumentPayload(JobPayload):
    type: Literal["PARSE_DOCUMENT", "OCR_DOCUMENT"]
    document_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    s3_key: str = Field(min_length=1)


class ExtractLegalDataPayload(JobPayload):
    type: Literal["EXTRACT_LEGAL_DATA", "EXTRACT_LEGAL_FACTS"]
    parsed_document_id: str = Field(min_length=1)


class PublishReviewPayload(JobPayload):
    type: Literal["PUBLISH_REVIEW"] = "PUBLISH_REVIEW"
    review_id: str = Field(min_length=1)


class ExportDraftPayload(JobPayload):
    type: Literal["EXPORT_DRAFT"] = "EXPORT_DRAFT"
    draft_id: str = Field(min_length=1)
    format: Literal["pdf", "docx"]


class BuildLexicalIndexPayload(JobPayload):
    type: Literal["BUILD_LEXICAL_INDEX"] = "BUILD_LEXICAL_INDEX"


class SyncMesaDocumentPayload(JobPayload):
    type: Literal["SYNC_MESA_DOCUMENT"] = "SYNC_MESA_DOCUMENT"
    parsed_document_id: str = Field(min_length=1)


class ProvisionMesaScopePayload(JobPayload):
    type: Literal["PROVISION_MESA_SCOPE"] = "PROVISION_MESA_SCOPE"
    binding_id: str = Field(min_length=1)


class PollMesaMutationPayload(JobPayload):
    type: Literal["POLL_MESA_MUTATION"] = "POLL_MESA_MUTATION"
    sync_record_id: str = Field(min_length=1)


SupportedPayload = Annotated[
    ScanDocumentPayload
    | ParseDocumentPayload
    | ExtractLegalDataPayload
    | PublishReviewPayload
    | ExportDraftPayload
    | BuildLexicalIndexPayload
    | SyncMesaDocumentPayload
    | ProvisionMesaScopePayload
    | PollMesaMutationPayload,
    Field(discriminator="type"),
]

payload_adapter: TypeAdapter[SupportedPayload] = TypeAdapter(SupportedPayload)


def validate_job_payload(job_type: str, payload: dict) -> dict:
    validated = payload_adapter.validate_python({**payload, "type": job_type})
    return validated.model_dump(exclude={"type"})


class JobExecutionError(RuntimeError):
    retryable = False


class RetryableJobError(JobExecutionError):
    retryable = True


class TerminalJobError(JobExecutionError):
    retryable = False


class LostLeaseError(JobExecutionError):
    retryable = True
