import asyncio
import websockets
import json
import jwt
import os
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
load_dotenv()
# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

print(f"🔑 WebSocket using Secret starting with: {JWT_SECRET[:4] if JWT_SECRET else 'None'}")

# Store connected clients
rooms = defaultdict(lambda: {'clients': set()})

async def authenticate(websocket, path):
    parsed_url = urlparse(path)
    room_name = parsed_url.path.strip('/')
    
    if not room_name:
        raise ValueError("No room specified")

    query_params = parse_qs(parsed_url.query)
    token_list = query_params.get('token', [])
    
    if not token_list:
        print(f"⚠️ No token provided for {room_name}")
        raise ValueError("Missing authentication token")

    token = token_list[0]
    
    try:
        # Verify using the SAME secret as Flask
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("userId") or payload.get("emailId") or payload.get("email")
        return room_name, user_id
        
    except jwt.ExpiredSignatureError:
        print(f"❌ Token Expired for room {room_name}")
        raise ValueError("Token expired")
    except jwt.InvalidTokenError as e:
        # Print the exact error to help debug (e.g., Signature verification failed)
        print(f"❌ Invalid Token Error: {str(e)}")
        raise ValueError("Invalid token")
    except Exception as e:
        print(f"❌ Unexpected Auth Error: {e}")
        raise ValueError("Authentication failed")

async def handle_client(websocket):
    try:
        # 1. Authenticate and determine room
        room, user_id = await authenticate(websocket, websocket.request.path)
        print(f"✅ User '{user_id}' joined room '{room}'")
        
    except ValueError as e:
        print(f"⛔ Auth failed: {e}")
        await websocket.close(code=4001, reason=str(e))
        return

    # 2. Add client to room
    rooms[room]['clients'].add(websocket)
    
    try:
        # NOTE: For Yjs, we DO NOT send a stored 'state' blindly on connect.
        # Yjs handles its own sync protocol (Step 1, Step 2).
        # As long as at least one other client is connected, they will sync.
        # If you need persistence when NO ONE is online, you need 'ypy-websocket'.
        
        async for message in websocket:
            # Broadcast message to ALL other clients in the room
            # Yjs clients will receive this and merge the updates automatically.
            
            # Debug Log
            print(f"📩 Received message ({len(message)} bytes) from {user_id} in {room}")
            
            disconnected = set()
            count = 0
            for client in rooms[room]['clients']:
                if client != websocket:
                    try:
                        await client.send(message)
                        count += 1
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.add(client)
            
            if count > 0:
                print(f"📢 Broadcasted to {count} clients")
            
            # Cleanup dead connections
            rooms[room]['clients'] -= disconnected

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        rooms[room]['clients'].discard(websocket)
        print(f"User '{user_id}' left room '{room}'")

async def main():
    print("🚀 WebSocket Server running on 0.0.0.0:5001")
    async with websockets.serve(handle_client, "0.0.0.0", 5001):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())