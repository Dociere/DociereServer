import uuid
import jwt
import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from instance.db import db

collaboration_bp = Blueprint('collaboration', __name__)

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

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
        project = db.get(project_id)  # Try without prefix
        if project:
            print(f"✓ Found project with key: {project_id}")
    except Exception as e:
        print(f"Tried without prefix: {e}")
    
    if not project:
        try:
            project = db.get(f"project:{project_id}")  # Try with prefix
            if project:
                print(f"✓ Found project with key: project:{project_id}")
        except Exception as e:
            print(f"Tried with prefix: {e}")
    
    if not project:
        print(f"✗ Project not found for ID: {project_id}")
        return jsonify({"error": "Project not found"}), 404
    
    # Debug: Print project structure
    print(f"Project data: {project}")
    
    project_owner = project.get("ownerId") or project.get("userId") or project.get("owner") or project.get("createdBy")
    
    if not project_owner:
        print("✗ No owner field found in project!")
        return jsonify({"error": "Project has no owner"}), 500
    
    print(f"Comparing: project_owner={project_owner} vs owner_id={owner_id}")
    
    if project_owner != owner_id:
        return jsonify({"error": "Not authorized"}), 403
    
    print("✓ Authorization successful!")
    
    data = request.json
    collaborator_email = data.get("collaboratorEmail")
    permissions = data.get("permissions", "edit")
    
    collab_token = jwt.encode({
        "projectId": project_id,
        "collaboratorEmail": collaborator_email,
        "permissions": permissions,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }, JWT_SECRET, ALGORITHM)
    
    share_link = f"http://localhost:5173/join/{collab_token}"
    
    return jsonify({
        "success": True,
        "shareToken": collab_token,
        "shareLink": share_link
    }), 200

@collaboration_bp.route('/projects/join/<token>', methods=['POST'])
def join_project(token):
    """Collaborator joins project using token"""
    auth_token = request.cookies.get("uid")
    
    try:
        # Verify user is authenticated
        user_payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = user_payload["userId"]
        
        # Verify share token
        share_payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        project_id = share_payload["projectId"]
        permissions = share_payload.get("permissions", "edit")
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Share link expired"}), 401
    except:
        return jsonify({"error": "Invalid token"}), 401
    
    # Add user as collaborator
    project_key = f"project:{project_id}"
    project = db.get(project_key)
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    # Check if already a collaborator
    collaborators = project.get("collaborators", [])
    if not any(c.get("userId") == user_id for c in collaborators):
        collaborators.append({
            "userId": user_id,
            "permissions": permissions,
            "joinedAt": datetime.now(timezone.utc).isoformat()
        })
        project["collaborators"] = collaborators
        db.save(project)
    
    return jsonify({
        "success": True,
        "project": {
            "projectId": project_id,
            "name": project.get("name"),
            "permissions": permissions
        }
    }), 200