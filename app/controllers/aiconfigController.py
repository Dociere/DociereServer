from instance.db import aiConfigDB, secretsDB
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from app.utils.encryption import encrypt


def _fetch_doc(db, doc_id):
    """Safely fetch a CouchDB doc. Returns the doc or None (never raises)."""
    try:
        return db[doc_id]
    except Exception:
        return None


def get_user_configs(user_id):
    try:
        doc = _fetch_doc(aiConfigDB, user_id)
        configs = doc.get("configs", []) if doc else []
        return JSONResponse(content={"success": True, "configs": configs}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


def save_user_configs(user_id, email, configs):
    now = datetime.now(timezone.utc).isoformat()
    try:
        # ── 1. Secrets storage ──────────────────────────────────────────────
        secrets_doc = _fetch_doc(secretsDB, user_id)
        is_new_secrets = secrets_doc is None

        if is_new_secrets:
            secrets_doc = {"_id": user_id, "ai_keys": {}}

        if "ai_keys" not in secrets_doc:
            secrets_doc["ai_keys"] = {}

        secrets_changed = False
        for config in configs:
            api_key = config.get("apiKey", "").strip()
            # Only store if it's a real new key (not the mask and not empty)
            if api_key and api_key != "********":
                secrets_doc["ai_keys"][config["id"]] = encrypt(api_key)
                secrets_changed = True
            # Always mask the key going into aiConfigDB
            config["apiKey"] = "********"

        if secrets_changed:
            secretsDB.save(secrets_doc)

        # ── 2. AI Configs storage (metadata only, keys masked) ──────────────
        existing_doc = _fetch_doc(aiConfigDB, user_id)
        if existing_doc is not None:
            existing_doc["configs"] = configs
            existing_doc["updated_at"] = now
            aiConfigDB.save(existing_doc)
        else:
            aiConfigDB.save({
                "_id": user_id,
                "userId": user_id,
                "emailId": email,
                "configs": configs,
                "created_at": now,
                "updated_at": now,
            })

        return JSONResponse(
            content={"success": True, "message": "Configs saved successfully"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)