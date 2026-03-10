from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.controllers.authController import register_user, login_user, check_auth_user, logout_user

auth_router = APIRouter()

@auth_router.post("/signup")
async def register(request: Request):
    data = await request.json()
    return register_user(data)

@auth_router.post("/login")
async def login(request: Request):
    data = await request.json()
    return login_user(data)

@auth_router.post("/signout")
async def logout():
    return logout_user()

@auth_router.get("/check-auth")
async def check_auth(request: Request):
    response, status = check_auth_user(request)
    return JSONResponse(content=response, status_code=status)