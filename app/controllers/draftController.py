from flask import request, jsonify
from datetime import datetime, timezone
from instance.db import draftsDB

def createDraft(project_id, data):
    content = data.get("content")

    if project_id in draftsDB:
        doc = draftsDB[project_id]
        doc["content"] = content
        draftsDB.save(doc)
    else:
        draftsDB.save({
            "_id": project_id,
            "content": content,
        })

    return jsonify({
        "success": True,
    }), 200