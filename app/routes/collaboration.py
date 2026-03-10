import uuid
import jwt
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from instance.db import projectsDB
import socket
import secrets
from threading import Timer
from instance.session_manager import verify_guest_access, verify_user_access
from app.controllers.authController import decode_jwt

collaboration_router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

guest_sessions = {} 

def get_local_ip():
    """Detects the actual LAN IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 1)) 
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

@collaboration_router.post('/projects/{project_id}/share')
async def create_share_token(project_id: str, request: Request):
    """Owner creates a share token for collaborator"""
    print(f"=== SHARE REQUEST ===")
    print(f"All cookies: {request.cookies}")
    
    auth_token = request.cookies.get("uid")
    print(f"UID token: {auth_token}")
    
    if not auth_token:
        print("✗ No auth token in cookies")
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    
    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
        owner_id = payload["userId"]
        print(f"✓ Owner ID from token: {owner_id}")
    except Exception as e:
        print(f"✗ Token decode error: {e}")
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    # Try to get project
    print(f"Looking for project: {project_id}")
    
    project = None
    try:
        project = projectsDB.get(project_id)
        if project:
            print(f"✓ Found project with key: {project_id}")
    except Exception as e:
        print(f"Tried without prefix: {e}")
    
    if not project:
        try:
            project = projectsDB.get(f"project:{project_id}")
            if project:
                print(f"✓ Found project with key: project:{project_id}")
        except Exception as e:
            print(f"Tried with prefix: {e}")
    
    if not project:
        print(f"✗ Project not found for ID: {project_id}")
        return JSONResponse(content={"error": "Project not found"}, status_code=404)
    
    print(f"Project data: {project}")
    
    data = await request.json()
    collaborator_email = data.get("collaboratorEmail")
    permissions = data.get("permissions", "edit")

    server_ip = os.getenv("SERVER_IP")
    if not server_ip or server_ip == "localhost":
        server_ip = get_local_ip()
        print(f"✓ Detected Share Server IP: {server_ip}")
    server_url = f"http://{server_ip}:5025"
    ws_url = f"ws://{server_ip}:5001"
    
    collab_token = jwt.encode({
        "projectId": project_id,
        "collaboratorEmail": collaborator_email,
        "permissions": permissions,
        "serverUrl": server_url,
        "wsUrl": ws_url,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }, JWT_SECRET, ALGORITHM)
    
    share_link = f"http://{server_ip}:5173/join/{collab_token}"
    
    return {
        "success": True,
        "shareToken": collab_token,
        "shareLink": share_link
    }

    
@collaboration_router.post('/projects/join/{token}')
async def join_project(token: str, request: Request):
    """Collaborator joins project using token"""
    print(f"=== JOIN REQUEST ===")
    
    auth_token = request.cookies.get("uid")
    print("auth_token", auth_token)
    is_guest = not auth_token
    
    try:
        share_payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        project_id = share_payload["projectId"]
        permissions = share_payload.get("permissions", "edit")
        
        print(f"✓ Share token valid - Project: {project_id}")
        
    except jwt.ExpiredSignatureError:
        return JSONResponse(content={"error": "Share link expired"}, status_code=401)
    except Exception as e:
        print(f"✗ Token decode error: {e}")
        return JSONResponse(content={"error": "Invalid token"}, status_code=401)
    
    project = projectsDB.get(project_id)
    if not project:
        return JSONResponse(content={"error": "Project not found"}, status_code=404)
    
    response_data = {
        "success": True,
        "project": {
            "projectId": project_id,
            "name": project.get("title"),
            "permissions": permissions
        }
    }
    
    # Handle authenticated user
    if not is_guest:
        try:
            user_payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
            user_id = user_payload["userId"]
            
            collaborators = project.get("collaborators", [])
            if not any(c.get("userId") == user_id for c in collaborators):
                collaborators.append({
                    "userId": user_id,
                    "permissions": permissions,
                    "joinedAt": datetime.now(timezone.utc).isoformat()
                })
                project["collaborators"] = collaborators
                projectsDB.save(project)
                print(f"✓ Added authenticated user {user_id} as collaborator")
            
            response_data["userType"] = "authenticated"
            response_data["userId"] = user_id
            
            return response_data
            
        except Exception as e:
            print(f"Auth token invalid, treating as guest: {e}")
            is_guest = True
    
    # Handle guest user
    if is_guest:
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        server_ip = os.getenv("SERVER_IP")
        if not server_ip or server_ip == "localhost":
            server_ip = get_local_ip()
        
        server_url = f"http://{server_ip}:5025"
        ws_url = f"ws://{server_ip}:5001"

        guest_token = jwt.encode({
            "projectId": project_id,
            "userId": guest_id,
            "permissions": permissions,
            "serverUrl": server_url,
            "wsUrl": ws_url,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET, ALGORITHM)
        
        guest_sessions[guest_token] = {
            "projectId": project_id,
            "permissions": permissions,
            "userId": guest_id,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"✓ Created guest JWT session: {guest_id}")
        
        response_data["userType"] = "guest"
        response_data["guestToken"] = guest_token
        
        return response_data

@collaboration_router.post('/projects/{project_id}/leave-session')
async def leave_session(project_id: str, request: Request):
    """Guest user explicitly leaves session"""
    guest_token = request.cookies.get("guest_session")
    
    if guest_token and guest_token in guest_sessions:
        del guest_sessions[guest_token]
        print(f"✓ Guest session {guest_token} ended")
    
    response = JSONResponse(content={"success": True}, status_code=200)
    response.set_cookie(key="guest_session", value="", max_age=0)
    
    return response


@collaboration_router.get('/projects/{project_id}/verify-access')
async def verify_access(project_id: str, request: Request):
    """Verify user has access to project (authenticated or guest session)"""
    auth_token = request.cookies.get("uid")
    guest_token = request.cookies.get("guest_session")
    
    # Check authenticated user
    if auth_token:
        try:
            user_payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
            user_id = user_payload["userId"]
            
            project = projectsDB.get(project_id)
            if not project:
                return JSONResponse(content={"access": False, "error": "Project not found"}, status_code=404)
            
            if project.get("owner") == user_id:
                return {"access": True, "role": "owner"}
            
            collaborators = project.get("collaborators", [])
            if any(c.get("userId") == user_id for c in collaborators):
                return {"access": True, "role": "collaborator"}
            
        except:
            pass
    
    # Check guest session
    if guest_token and guest_token in guest_sessions:
        session = guest_sessions[guest_token]
        if session["projectId"] == project_id:
            return {
                "access": True,
                "role": "guest",
                "permissions": session["permissions"]
            }
    
    return JSONResponse(content={"access": False}, status_code=403)

@collaboration_router.get('/projects/{project_id}')
async def get_project(project_id: str):
    print(f"=== GET PROJECT REQUEST ===")
    print(f"Project ID: {project_id}")
    
    project = projectsDB.get(project_id)
    if not project:
        return JSONResponse(content={"error": "Project not found"}, status_code=404)
    
    print(project)
    
    return {
        "id": project.get("_id"),
        "title": project.get("title"),
        "files": project.get("files", {}),
        "activeFile": project.get("activeFile"),
        "owner": project.get("owner"),
        "created": project.get("created"),
        "modified": project.get("modified")
    }


def cleanup_inactive_sessions():
    """Remove guest sessions older than 24 hours"""
    now = datetime.now(timezone.utc)
    expired = []
    
    for token, session in guest_sessions.items():
        created = datetime.fromisoformat(session["createdAt"])
        if (now - created).total_seconds() > 86400:
            expired.append(token)
    
    for token in expired:
        del guest_sessions[token]
    
    print(f"Cleaned up {len(expired)} expired guest sessions")
    Timer(3600, cleanup_inactive_sessions).start()

# Start cleanup when server starts
cleanup_inactive_sessions()


@collaboration_router.post('/projects/{project_id}/get-collab-token')
async def get_collaboration_token(project_id: str, request: Request):
    """
    Generates a JWT token for Owners AND Collaborators.
    """
    
    # 1. AUTHENTICATION
    auth_token = request.cookies.get("uid")
    if not auth_token:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    
    try:
        user_payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
        requester_email = user_payload.get("emailId")
    except Exception as e:
        return JSONResponse(content={"error": "Invalid auth token"}, status_code=401)
    
    # 2. FETCH PROJECT
    project = projectsDB.get(project_id) or projectsDB.get(f"project:{project_id}")
    if not project:
        return JSONResponse(content={"error": "Project not found"}, status_code=404)
    
    
    # 3. VERIFY PERMISSIONS
    owner_email = project.get("owner")
    
    collaborators = project.get("collaborators", [])

    is_collaborator = any(c.get("userId") == requester_email for c in collaborators)
    
    is_owner = (owner_email == requester_email)

    if not is_owner and not is_collaborator:
        print(f"⛔ Access Denied: {requester_email} is neither owner nor collaborator.")
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    # 4. SERVER DISCOVERY
    server_ip = os.getenv("SERVER_IP")
    if not server_ip or server_ip == "localhost":
         server_ip = get_local_ip()
         print(f"✓ Detected Owner Server IP: {server_ip}") 

    server_url = f"http://{server_ip}:5025"
    ws_url = f"ws://{server_ip}:5001"

    # 5. GENERATE JWT
    token_payload = {
        "projectId": project_id,
        "userId": requester_email,
        "permissions": "owner" if is_owner else "edit",
        "serverUrl": server_url,
        "wsUrl": ws_url,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }

    collab_token = jwt.encode(token_payload, JWT_SECRET, ALGORITHM)
    
    return {
        "success": True,
        "collaborationToken": collab_token,
        "serverUrl": server_url,
        "wsUrl": ws_url
    }