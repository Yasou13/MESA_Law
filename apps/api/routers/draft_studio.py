from fastapi import APIRouter
router = APIRouter()
@router.post("/drafts/autosave")
async def autosave():
    return {"status": "saved"}\n