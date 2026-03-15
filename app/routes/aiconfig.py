from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.controllers.authController import check_auth_user
from app.controllers.aiconfigController import get_user_configs, save_user_configs
from instance.db import secretsDB
from app.utils.encryption import decrypt

aiconfig_router = APIRouter()

def _get_auth_user(request: Request):
    """Returns (user_id, email, None) on success, or (None, None, JSONResponse) on failure."""
    auth_result = check_auth_user(request)
    if isinstance(auth_result, tuple):
        response_data, status = auth_result
        if status != 200:
            return None, None, JSONResponse(content=response_data, status_code=status)
        user = response_data.get("user", {})
        return user.get("userId"), user.get("emailId"), None
    return None, None, JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)


@aiconfig_router.get("/aiconfigs")
async def fetch_configs(request: Request):
    user_id, _, err = _get_auth_user(request)
    if err:
        return err
    return get_user_configs(user_id)


@aiconfig_router.post("/aiconfigs")
async def update_configs(request: Request):
    user_id, email, err = _get_auth_user(request)
    if err:
        return err

    data = await request.json()
    configs = data.get("configs", [])
    return save_user_configs(user_id, email, configs)


@aiconfig_router.get("/aiconfigs/secret/{config_id}")
async def fetch_secret(config_id: str, request: Request):
    user_id, _, err = _get_auth_user(request)
    if err:
        return err

    try:
        # python-couchdb raises ResourceNotFound on db[key] if doc doesn't exist.
        # Use try/except rather than `in` check to avoid TOCTOU race.
        try:
            secrets_doc = secretsDB[user_id]
        except Exception:
            return JSONResponse(
                content={"success": False, "error": "No secrets found for this user"},
                status_code=404
            )

        ai_keys = secrets_doc.get("ai_keys", {})
        encrypted_key = ai_keys.get(config_id)

        if not encrypted_key:
            return JSONResponse(
                content={"success": False, "error": "Secret not found for this config"},
                status_code=404
            )

        real_key = decrypt(encrypted_key)

        if real_key is None:
            return JSONResponse(
                content={"success": False, "error": "Failed to decrypt key"},
                status_code=500
            )

        return JSONResponse(content={"success": True, "apiKey": real_key}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)