import uuid
import jwt
import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, make_response
from instance.db import projectsDB
import socket
import secrets
from threading import Timer
from instance.session_manager import verify_guest_access, verify_user_access
# from instance.session_manager import guest_sessions
from app.controllers.authController import decode_jwt

collaboration_bp = Blueprint('collaboration', __name__)

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

guest_sessions = {} 

def get_local_ip():
    """Detects the actual LAN IP address of this machine"""
    try:
        # Create a dummy socket to connect to Google DNS (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 1)) 
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

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
    
    # This usually does not get trigerred thus can be removed
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
    # Dynamically detect server IP
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
    
    # IMPORTANT: Share link points to Laptop 1's IP, not localhost
    share_link = f"http://{server_ip}:5173/join/{collab_token}"
    
    return jsonify({
        "success": True,
        "shareToken": collab_token,
        "shareLink": share_link
    }), 200

    
@collaboration_bp.route('/projects/join/<token>', methods=['POST'])
def join_project(token):
    """Collaborator joins project using token"""
    print(f"=== JOIN REQUEST ===")
    
    auth_token = request.cookies.get("uid")
    print("auth_token", auth_token)
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
            
            # Add to project collaborators
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
            
            return jsonify(response_data), 200
            
        except Exception as e:
            print(f"Auth token invalid, treating as guest: {e}")
            is_guest = True
    
    # Handle guest user - ALWAYS create response with cookie
    if is_guest:
        # Create a unique guest ID
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        # Dynamically detect server IP
        server_ip = os.getenv("SERVER_IP")
        if not server_ip or server_ip == "localhost":
            server_ip = get_local_ip()
        
        server_url = f"http://{server_ip}:5025"
        ws_url = f"ws://{server_ip}:5001"

        # Generate JWT for guest (Standardized format)
        guest_token = jwt.encode({
            "projectId": project_id,
            "userId": guest_id,
            "permissions": permissions,
            "serverUrl": server_url,
            "wsUrl": ws_url,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET, ALGORITHM)
        
        # We can still track session metadata if needed, but the JWT is the authority
        # FIXME: Delete the below code if theres no dependency
        guest_sessions[guest_token] = {
            "projectId": project_id,
            "permissions": permissions,
            "userId": guest_id,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"✓ Created guest JWT session: {guest_id}")
        
        response_data["userType"] = "guest"
        response_data["guestToken"] = guest_token  # Return in body
        
        return jsonify(response_data), 200

@collaboration_bp.route('/projects/<project_id>/leave-session', methods=['POST'])
def leave_session(project_id):
    """Guest user explicitly leaves session"""
    guest_token = request.cookies.get("guest_session")
    
    if guest_token and guest_token in guest_sessions:
        del guest_sessions[guest_token]
        print(f"✓ Guest session {guest_token} ended")
    
    response = make_response(jsonify({"success": True}), 200)
    response.set_cookie("guest_session", "", expires=0)  # Clear cookie
    
    return response


@collaboration_bp.route('/projects/<project_id>/verify-access', methods=['GET'])
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

@collaboration_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    print(f"=== GET PROJECT REQUEST ===")
    print(f"Project ID: {project_id}")
    
    # auth_token = request.cookies.get("uid")
    # guest_token = request.headers.get("X-Guest-Token")  # From header instead
    
    # print(f"Auth token: {auth_token is not None}")
    # print(f"Guest token from header: {guest_token}")
    
    # has_access = False
    
    # Get project
    project = projectsDB.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    print(project)
    
    # Check authenticated user
    # if auth_token:
    #     try:
    #         user_payload = decode_jwt(auth_token)
    #         user_id = user_payload["userId"]
    #         has_access = verify_user_access(user_id, project, projectsDB)
    #     except:
    #         pass
    
    # # Check guest session from header
    # if not has_access and guest_token:
    #     print(f"Checking guest token: {guest_token}")
    #     has_access = verify_guest_access(guest_token, project_id)
    #     print(f"Guest access: {has_access}")
    
    # if not has_access:
    #     print("❌ Access denied")
    #     return jsonify({"error": "Access denied"}), 403
    
    # print("✅ Access granted")
    
    return jsonify({
        "id": project.get("_id"),
        "title": project.get("title"),
        "files": project.get("files", {}),
        "activeFile": project.get("activeFile"),
        "owner": project.get("owner"),
        "created": project.get("created"),
        "modified": project.get("modified")
    }), 200


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


@collaboration_bp.route('/projects/<project_id>/get-collab-token', methods=['POST'])
def get_collaboration_token(project_id):
    """
    Generates a JWT token for Owners AND Collaborators.
    """
    
    # 1. AUTHENTICATION
    auth_token = request.cookies.get("uid")
    if not auth_token:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        user_payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
        requester_email = user_payload.get("emailId")
    except Exception as e:
        return jsonify({"error": "Invalid auth token"}), 401
    
    # 2. FETCH PROJECT
    project = projectsDB.get(project_id) or projectsDB.get(f"project:{project_id}")
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    
    # 3. VERIFY PERMISSIONS
    owner_email = project.get("owner")
    
    # Check if user is in the collaborators list
    collaborators = project.get("collaborators", [])

    is_collaborator = any(c.get("userId") == requester_email for c in collaborators)
    
    is_owner = (owner_email == requester_email)

    if not is_owner and not is_collaborator:
        print(f"⛔ Access Denied: {requester_email} is neither owner nor collaborator.")
        return jsonify({"error": "Access denied"}), 403

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
        "permissions": "owner" if is_owner else "edit", # <--- DYNAMIC PERMISSIONS
        "serverUrl": server_url,
        "wsUrl": ws_url,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }

    collab_token = jwt.encode(token_payload, JWT_SECRET, ALGORITHM)
    
    return jsonify({
        "success": True,
        "collaborationToken": collab_token,
        "serverUrl": server_url,
        "wsUrl": ws_url
    }), 200