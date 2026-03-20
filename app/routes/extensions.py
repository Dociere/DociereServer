from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import json

extensions_router = APIRouter()

EXTENSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "extensions")

@extensions_router.get("/extensions")
async def get_extensions():
    registry_path = os.path.join(EXTENSIONS_DIR, "registry.json")
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, "r") as f:
        return json.load(f)

@extensions_router.get("/extensions/download/{extension_id}")
async def download_extension(extension_id: str):
    zip_path = os.path.join(EXTENSIONS_DIR, f"{extension_id}.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Extension not found")
    return FileResponse(zip_path, media_type="application/zip", filename=f"{extension_id}.zip")
