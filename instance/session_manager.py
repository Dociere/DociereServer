from datetime import datetime, timezone

# In-memory storage for guest sessions
# In production, use Redis or similar
guest_sessions = {}

def verify_guest_access(guest_token, project_id):
    """Check if guest token has access to project"""
    if not guest_token or guest_token not in guest_sessions:
        return False
    
    session = guest_sessions[guest_token]
    return session["projectId"] == project_id

def verify_user_access(user_id, project, projectsDB):
    """Check if authenticated user has access to project"""
    if not project:
        return False
    
    # Check if owner
    if project.get("owner") == user_id:
        return True
    
    # Check if collaborator
    collaborators = project.get("collaborators", [])
    return any(c.get("userId") == user_id for c in collaborators)