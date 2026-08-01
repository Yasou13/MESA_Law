import re

from pydantic import BaseModel, Field, field_validator


def sanitize_text(v: str) -> str:
    # Basic XSS prevention: remove script tags and on* attributes
    v = re.sub(r"<script.*?>.*?</script>", "", v, flags=re.IGNORECASE | re.DOTALL)
    v = re.sub(r'on\w+=".*?"', "", v, flags=re.IGNORECASE)
    return v.strip()


class MatterCreate(BaseModel):
    title: str = Field(
        ..., min_length=3, max_length=255, description="The title of the matter"
    )
    internal_reference: str | None = Field(None, description="Internal reference ID")
    client_name: str | None = Field(None, description="Client name")
    jurisdiction: str | None = Field(None, description="The jurisdiction of the matter")
    case_type: str | None = Field(None, description="Type of case")
    confidentiality_level: str = Field("standard", description="Confidentiality level")
    ai_processing_policy: str = Field("standard", description="AI processing policy")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return sanitize_text(v)


class MatterResponse(BaseModel):
    id: str
    title: str
    internal_reference: str | None = None
    status: str
    client_name: str | None = None
    jurisdiction: str | None = None
    case_type: str | None = None
    confidentiality_level: str
    ai_processing_policy: str
    opened_at: str | None = None
    closed_at: str | None = None
    access_scope: str | None = None


class UploadIntentRequest(BaseModel):
    matter_id: str
    filename: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=100)
    size_bytes: int = Field(
        ..., gt=0, le=100 * 1024 * 1024, description="File size in bytes"
    )

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        return sanitize_text(v)


class UploadIntentResponse(BaseModel):
    document_id: str
    revision_id: str
    presigned_url: str
    storage_key: str


class DocumentResponse(BaseModel):
    id: str
    title: str
    status: str | None = "clean"


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class SourceLocator(BaseModel):
    document_id: str
    page_number: int
    bbox: BoundingBox | None = None
    text_snippet: str | None = None
