from fastapi import APIRouter, Request

from app.controllers.citationController import saveCitations, getCitations

citation_router = APIRouter()

@citation_router.put("/citations/{user_id}/{project_id}")
async def save_citations_sync(user_id: str, project_id: str, request: Request):
    data = await request.json()
    return saveCitations(user_id, project_id, data)

@citation_router.get("/citations/{user_id}/{project_id}")
async def get_citations_sync(user_id: str, project_id: str):
    return getCitations(user_id, project_id)
