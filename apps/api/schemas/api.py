import re
from pydantic import BaseModel, Field, field_validator

def sanitize_text(v: str) -> str:
    # Basic XSS prevention: remove script tags and on* attributes
    v = re.sub(r'<script.*?>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
    v = re.sub(r'on\w+=".*?"', '', v, flags=re.IGNORECASE)
    return v.strip()

class MatterCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="The title of the matter")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        return sanitize_text(v)

class MatterResponse(BaseModel):
    id: str
    title: str
    status: str

class UploadIntentRequest(BaseModel):
    matter_id: str
    filename: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=100)
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        return sanitize_text(v)

class UploadIntentResponse(BaseModel):
    document_id: str
    revision_id: str
    presigned_url: str

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
