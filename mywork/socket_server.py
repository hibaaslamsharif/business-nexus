import socketio
import uvicorn
from fastapi import FastAPI
from datetime import datetime
from pymongo import MongoClient
import json

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['business_nexus_chat']
messages_collection = db['messages']

# Create FastAPI app
app = FastAPI()

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode='asgi'
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    await sio.emit('connected', {'message': 'Connected to chat server'}, room=sid)

@sio.event
async def join_room(sid, data):
    """Join a chat room between two users"""
    user_id = data.get('user_id')
    other_user_id = data.get('other_user_id')
    
    # Create consistent room name (smaller ID first)
    room_name = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    
    await sio.enter_room(sid, room_name)
    print(f"User {user_id} joined room {room_name}")
    
    await sio.emit('joined_room', {
        'room': room_name,
        'message': f'Joined chat room'
    }, room=sid)

@sio.event
async def send_message(sid, data):
    """Send and save a message"""
    try:
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')
        message_text = data.get('message')
        sender_name = data.get('sender_name', 'Unknown')
        
        # Create consistent room name
        room_name = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        
        # Create message document
        message_doc = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message_text,
            'sender_name': sender_name,
            'timestamp': datetime.utcnow(),
            'room': room_name
        }
        
        # Save to MongoDB
        result = messages_collection.insert_one(message_doc)
        message_doc['_id'] = str(result.inserted_id)
        message_doc['timestamp'] = message_doc['timestamp'].isoformat()
        
        # Emit to all users in the room
        await sio.emit('receive_message', message_doc, room=room_name)
        
        print(f"Message sent from {sender_id} to {receiver_id}: {message_text}")
        
    except Exception as e:
        print(f"Error sending message: {e}")
        await sio.emit('error', {'message': 'Failed to send message'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

if __name__ == "__main__":
    uvicorn.run("socket_server:socket_app", host="127.0.0.1", port=5000, reload=True)
