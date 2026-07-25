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
