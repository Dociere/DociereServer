from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import jwt
import os
from datetime import datetime, timezone
from instance.db import userDB
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "*"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# Store active connections and document states
active_rooms = {}  # roomId -> {users: set(), yjs_state: bytes}

def verify_token(token):
    """Verify JWT token and return userId"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("userId")
    except:
        return None

def verify_project_access(project_id, user_id):
    """Check if user has access to project (owner or collaborator)"""
    try:
        project = userDB.get(f"project:{project_id}")
        if not project:
            return False, None
        
        # Check if owner
        if project.get("ownerId") == user_id:
            return True, "owner"
        
        # Check if collaborator
        collaborators = project.get("collaborators", [])
        for collab in collaborators:
            if collab.get("userId") == user_id:
                return True, "collaborator"
        
        return False, None
    except:
        return False, None

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('join_project')
def handle_join_project(data):
    """Join a project room for collaboration"""
    token = data.get('token')
    project_id = data.get('projectId')
    
    user_id = verify_token(token)
    if not user_id:
        emit('error', {'message': 'Invalid token'})
        return
    
    has_access, role = verify_project_access(project_id, user_id)
    if not has_access:
        emit('error', {'message': 'Access denied'})
        return
    
    room = f"project:{project_id}"
    join_room(room)
    
    # Track active users
    if room not in active_rooms:
        active_rooms[room] = {'users': set(), 'yjs_state': None}
    
    active_rooms[room]['users'].add(request.sid)
    
    # Send initial state if exists
    if active_rooms[room]['yjs_state']:
        emit('sync_state', {'state': active_rooms[room]['yjs_state']})
    
    # Notify others
    emit('user_joined', {
        'userId': user_id,
        'role': role,
        'userCount': len(active_rooms[room]['users'])
    }, room=room, skip_sid=request.sid)
    
    print(f"User {user_id} joined project {project_id} as {role}")

@socketio.on('yjs_update')
def handle_yjs_update(data):
    """Broadcast Yjs updates to all clients in the room"""
    project_id = data.get('projectId')
    update = data.get('update')  # Binary Yjs update
    
    room = f"project:{project_id}"
    
    # Store latest state
    if room in active_rooms:
        active_rooms[room]['yjs_state'] = update
    
    # Broadcast to all other clients
    emit('yjs_update', {'update': update}, room=room, skip_sid=request.sid)

@socketio.on('leave_project')
def handle_leave_project(data):
    project_id = data.get('projectId')
    room = f"project:{project_id}"
    
    leave_room(room)
    
    if room in active_rooms:
        active_rooms[room]['users'].discard(request.sid)
        
        if len(active_rooms[room]['users']) == 0:
            # Save to CouchDB before removing
            save_project_to_db(project_id, active_rooms[room]['yjs_state'])
            del active_rooms[room]
    
    emit('user_left', {'userCount': len(active_rooms.get(room, {}).get('users', []))}, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    
    # Remove from all rooms
    for room, data in list(active_rooms.items()):
        if request.sid in data['users']:
            data['users'].discard(request.sid)
            emit('user_left', {'userCount': len(data['users'])}, room=room)
            
            if len(data['users']) == 0:
                project_id = room.replace('project:', '')
                save_project_to_db(project_id, data['yjs_state'])
                del active_rooms[room]

def save_project_to_db(project_id, yjs_state):
    """Save Yjs state to CouchDB"""
    try:
        project_key = f"project:{project_id}"
        project = userDB.get(project_key, {})
        project['yjsState'] = yjs_state.hex() if yjs_state else None
        project['lastModified'] = datetime.now(timezone.utc).isoformat()
        userDB.save(project)
        print(f"Saved project {project_id} to database")
    except Exception as e:
        print(f"Error saving project: {e}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)