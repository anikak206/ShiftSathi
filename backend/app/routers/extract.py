from fastapi import APIRouter
from pydantic import BaseModel
from ..services.llm import extract as llm_extract

router = APIRouter(prefix="/api/extract", tags=["extract"])

class ExtractReq(BaseModel):
    transcript: str

@router.post("")
async def extract(req: ExtractReq):
    return await llm_extract(req.transcript)
