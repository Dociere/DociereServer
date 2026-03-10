from datetime import datetime, timezone
from instance.db import projectsDB

def saveProject(project_id, data):
    title = data.get("title")
    files = data.get("files")
    owner = data.get("owner")
    activeFile = data.get("activeFile")

    now = datetime.now(timezone.utc).isoformat()

    if project_id in projectsDB:
        doc = projectsDB[project_id]
        doc["files"] = files
        doc["title"] = title
        doc["owner"] = owner
        doc["activeFile"] = activeFile
        doc["modified"] = now
        projectsDB.save(doc)
    else:
        projectsDB.save({
            "_id": project_id,
            "title": title,
            "created": now,
            "modified": now,
            "files": files,
            "activeFile": activeFile,
            "owner": owner,
        })

    return {"success": True}