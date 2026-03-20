from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    try:
        from google import genai
        has_ai = True
    except ImportError:
        has_ai = False

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher
        has_crypto = True
    except ImportError:
        has_crypto = False

    try:
        import bcrypt
        has_bcrypt = True
    except ImportError:
        has_bcrypt = False

    return {
        "status": "ok", 
        "message": "Server is running",
        "features": {
            "ai_gemini": has_ai,
            "encryption": has_crypto,
            "auth_bcrypt": has_bcrypt,
            "extensions": True
        }
    }
