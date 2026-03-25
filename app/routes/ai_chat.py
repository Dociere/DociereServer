from fastapi import APIRouter, Request

from app.controllers.aiChatController import saveChat, getChat

ai_chat_router = APIRouter()

@ai_chat_router.put("/ai-chat/{user_id}/{project_id}")
async def save_ai_chat(user_id: str, project_id: str, request: Request):
    data = await request.json()
    return saveChat(user_id, project_id, data)

@ai_chat_router.get("/ai-chat/{user_id}/{project_id}")
async def get_ai_chat(user_id: str, project_id: str):
    return getChat(user_id, project_id)
