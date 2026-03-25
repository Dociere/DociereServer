from datetime import datetime, timezone
from instance.db import aiChatDB

def saveChat(user_id, project_id, data):
    messages = data.get("messages", [])
    doc_id = f"{user_id}:{project_id}"
    now = datetime.now(timezone.utc).isoformat()

    if doc_id in aiChatDB:
        doc = aiChatDB[doc_id]
        doc["messages"] = messages
        doc["modified"] = now
        aiChatDB.save(doc)
    else:
        aiChatDB.save({
            "_id": doc_id,
            "userId": user_id,
            "projectId": project_id,
            "messages": messages,
            "created": now,
            "modified": now,
        })

    return {"success": True}

def getChat(user_id, project_id):
    doc_id = f"{user_id}:{project_id}"

    if doc_id in aiChatDB:
        doc = aiChatDB[doc_id]
        return {
            "success": True,
            "messages": doc.get("messages", []),
            "modified": doc.get("modified"),
        }
    else:
        return {"success": True, "messages": []}
