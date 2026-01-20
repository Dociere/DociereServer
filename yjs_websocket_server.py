import asyncio
import websockets
import json
from collections import defaultdict

# Store document states
rooms = defaultdict(lambda: {'clients': set(), 'state': None})

async def handle_client(websocket):
    """Handle WebSocket connection from Yjs client"""
    path = websocket.request.path
    print(f"New connection: {path}")
    
    # Extract room from path (e.g., /project:xxx)
    room = path.strip('/')
    
    # Add client to room
    rooms[room]['clients'].add(websocket)
    print(f"Client joined room: {room}. Total clients: {len(rooms[room]['clients'])}")
    
    try:
        # Send existing state to new client if available
        if rooms[room]['state']:
            await websocket.send(rooms[room]['state'])
        
        # Listen for messages
        async for message in websocket:
            # Store latest state
            rooms[room]['state'] = message
            
            # Broadcast to all other clients in the room
            disconnected = set()
            for client in rooms[room]['clients']:
                if client != websocket:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.add(client)
            
            # Clean up disconnected clients
            rooms[room]['clients'] -= disconnected
            
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected from {room}")
    finally:
        # Remove client from room
        rooms[room]['clients'].discard(websocket)
        print(f"Client left room: {room}. Remaining: {len(rooms[room]['clients'])}")

async def main():
    print("Starting WebSocket server on ws://0.0.0.0:5001")
    async with websockets.serve(handle_client, "0.0.0.0", 5001):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())