from datetime import datetime, timezone
from instance.db import citationsDB

def saveCitations(user_id, project_id, data):
    items = data.get("items", [])
    doc_id = f"{user_id}:{project_id}"
    now = datetime.now(timezone.utc).isoformat()

    if doc_id in citationsDB:
        doc = citationsDB[doc_id]
        doc["items"] = items
        doc["modified"] = now
        citationsDB.save(doc)
    else:
        citationsDB.save({
            "_id": doc_id,
            "userId": user_id,
            "projectId": project_id,
            "items": items,
            "created": now,
            "modified": now,
        })
    return {"success": True}

def getCitations(user_id, project_id):
    doc_id = f"{user_id}:{project_id}"
    if doc_id in citationsDB:
        doc = citationsDB[doc_id]
        return {
            "success": True,
            "items": doc.get("items", []),
            "modified": doc.get("modified"),
        }
    return {"success": True, "items": []}
