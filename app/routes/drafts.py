from fastapi import APIRouter, Request

from app.controllers.draftController import createDraft

draft_router = APIRouter()

@draft_router.put("/drafts/{project_id}")
async def create_draft(project_id: str, request: Request):
    data = await request.json()
    return createDraft(project_id, data)