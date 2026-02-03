from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import llm_service
from app.services.embeddings import embedding_service

router = APIRouter()


class LlmEndpointUpdate(BaseModel):
    endpoint: str


@router.get("/endpoint")
async def get_endpoint():
    return {
        "endpoint": llm_service.get_endpoint(),
        "embedding_endpoint": embedding_service.get_endpoint(),
    }


@router.post("/endpoint")
async def set_endpoint(payload: LlmEndpointUpdate):
    endpoint = payload.endpoint.strip()
    if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        raise HTTPException(status_code=400, detail="Endpoint must start with http:// or https://")
    llm_service.set_endpoint(endpoint)
    embedding_service.set_endpoint(endpoint)
    return {"endpoint": endpoint}
