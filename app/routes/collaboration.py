import uuid
import jwt
import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, make_response
from instance.db import projectsDB
import socket
import secrets
from threading import Timer

collaboration_bp = Blueprint('collaboration', __name__)

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

guest_sessions = {} 

@collaboration_bp.route('/projects/<project_id>/share', methods=['POST'])
def create_share_token(project_id):
    """Owner creates a share token for collaborator"""
    print(f"=== SHARE REQUEST ===")
    print(f"All cookies: {request.cookies}")
    
    auth_token = request.cookies.get("uid")
    print(f"UID token: {auth_token}")
    
    if not auth_token:
        print("✗ No auth token in cookies")
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
        owner_id = payload["userId"]
        print(f"✓ Owner ID from token: {owner_id}")
    except Exception as e:
        print(f"✗ Token decode error: {e}")
        return jsonify({"error": "Unauthorized"}), 401
    
    # Try to get project
    print(f"Looking for project: {project_id}")
    
    project = None
    try:
        project = projectsDB.get(project_id)  # Try without prefix
        if project:
            print(f"✓ Found project with key: {project_id}")
    except Exception as e:
        print(f"Tried without prefix: {e}")
    
    if not project:
        try:
            project = projectsDB.get(f"project:{project_id}")  # Try with prefix
            if project:
                print(f"✓ Found project with key: project:{project_id}")
        except Exception as e:
            print(f"Tried with prefix: {e}")
    
    if not project:
        print(f"✗ Project not found for ID: {project_id}")
        return jsonify({"error": "Project not found"}), 404
    
    # Debug: Print project structure
    print(f"Project data: {project}")
    
    # project_owner = project.get("owner")
    
    # if not project_owner:
    #     print("✗ No owner field found in project!")
    #     return jsonify({"error": "Project has no owner"}), 500
    
    # print(f"Comparing: project_owner={project_owner} vs owner_id={owner_id}")
    
    # if project_owner != owner_id:
    #     return jsonify({"error": "Not authorized"}), 403
    
    # print("✓ Authorization successful!")
    
    data = request.json
    collaborator_email = data.get("collaboratorEmail")
    permissions = data.get("permissions", "edit")

    # Get Laptop 1's actual IP (not localhost)
    # laptop1_ip = socket.gethostbyname(socket.gethostname())
    
    # Or use environment variable for better control
    # server_ip = os.getenv("SERVER_IP", laptop1_ip)
    server_ip = os.getenv("SERVER_IP")
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
    
    # IMPORTANT: Share link points to Laptop 1's IP, not localhost
    share_link = f"http://{server_ip}:5173/join/{collab_token}"
    
    return jsonify({
        "success": True,
        "shareToken": collab_token,
        "shareLink": share_link
    }), 200

    
@collaboration_bp.route('/api/projects/join/<token>', methods=['POST'])
def join_project(token):
    """Collaborator joins project using token"""
    print(f"=== JOIN REQUEST ===")
    
    auth_token = request.cookies.get("uid")
    is_guest = not auth_token
    
    try:
        # Verify share token
        share_payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        project_id = share_payload["projectId"]
        permissions = share_payload.get("permissions", "edit")
        
        print(f"✓ Share token valid - Project: {project_id}")
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Share link expired"}), 401
    except Exception as e:
        print(f"✗ Token decode error: {e}")
        return jsonify({"error": "Invalid token"}), 401
    
    # Check if project exists
    project = projectsDB.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
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
            
            # Add to project collaborators (persistent)
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
            
        except Exception as e:
            print(f"Auth token invalid, treating as guest: {e}")
            is_guest = True
    
    # Handle guest user
    if is_guest:
        # Create temporary guest session
        guest_token = secrets.token_urlsafe(32)
        guest_sessions[guest_token] = {
            "projectId": project_id,
            "permissions": permissions,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"✓ Created guest session: {guest_token}")
        
        response_data["userType"] = "guest"
        response_data["guestToken"] = guest_token
        
        # Set guest session cookie (expires on browser close)
        response = make_response(jsonify(response_data), 200)
        response.set_cookie(
            "guest_session",
            guest_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=None  # Session cookie - expires on tab close
        )
        return response
    
    return jsonify(response_data), 200

@collaboration_bp.route('/api/projects/<project_id>/leave-session', methods=['POST'])
def leave_session(project_id):
    """Guest user explicitly leaves session"""
    guest_token = request.cookies.get("guest_session")
    
    if guest_token and guest_token in guest_sessions:
        del guest_sessions[guest_token]
        print(f"✓ Guest session {guest_token} ended")
    
    response = make_response(jsonify({"success": True}), 200)
    response.set_cookie("guest_session", "", expires=0)  # Clear cookie
    
    return response


@collaboration_bp.route('/api/projects/<project_id>/verify-access', methods=['GET'])
def verify_access(project_id):
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
                return jsonify({"access": False, "error": "Project not found"}), 404
            
            # Check if owner
            if project.get("owner") == user_id:
                return jsonify({"access": True, "role": "owner"}), 200
            
            # Check if collaborator
            collaborators = project.get("collaborators", [])
            if any(c.get("userId") == user_id for c in collaborators):
                return jsonify({"access": True, "role": "collaborator"}), 200
            
        except:
            pass
    
    # Check guest session
    if guest_token and guest_token in guest_sessions:
        session = guest_sessions[guest_token]
        if session["projectId"] == project_id:
            return jsonify({
                "access": True,
                "role": "guest",
                "permissions": session["permissions"]
            }), 200
    
    return jsonify({"access": False}), 403


def cleanup_inactive_sessions():
    """Remove guest sessions older than 24 hours"""
    now = datetime.now(timezone.utc)
    expired = []
    
    for token, session in guest_sessions.items():
        created = datetime.fromisoformat(session["createdAt"])
        if (now - created).total_seconds() > 86400:  # 24 hours
            expired.append(token)
    
    for token in expired:
        del guest_sessions[token]
    
    print(f"Cleaned up {len(expired)} expired guest sessions")
    Timer(3600, cleanup_inactive_sessions).start()  # Run every hour

# Start cleanup when server starts
cleanup_inactive_sessions()