from pydantic import BaseModel


class MatterCreate(BaseModel):
    title: str

class MatterResponse(BaseModel):
    id: str
    title: str
    status: str

class UploadIntentRequest(BaseModel):
    matter_id: str
    filename: str
    mime_type: str

class UploadIntentResponse(BaseModel):
    document_id: str
    revision_id: str
    presigned_url: str

class DocumentResponse(BaseModel):
    id: str
    title: str

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
