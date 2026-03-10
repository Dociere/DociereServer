from fastapi import APIRouter, Request
from app.controllers.projectController import saveProject

project_router = APIRouter()

@project_router.put("/projects/{project_id}")
async def save_project(project_id: str, request: Request):
    data = await request.json()
    return saveProject(project_id, data)