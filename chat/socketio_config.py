import asyncio
import os
import json
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
import socketio
from .models import Message

# Get user model
User = get_user_model()

# The sio instance will be created in socketio_server.py
# This allows us to import it here and attach event handlers
sio = None  # Will be set by socketio_server.py

def get_room_name(user1_id, user2_id):
    """Generate a consistent room name for a pair of users"""
    return f"chat_{min(int(user1_id), int(user2_id))}_{max(int(user1_id), int(user2_id))}"

@sio.event
async def connect(sid, environ, auth):
    """Handle new socket connection"""
    try:
        # For aiohttp, we need to get user from the session
        from django.contrib.sessions.models import Session
        from django.contrib.auth.models import AnonymousUser
        
        session_key = environ.get('HTTP_COOKIE', '').split('sessionid=')[-1].split(';')[0]
        if session_key:
            session = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: Session.objects.get(session_key=session_key)
            )
            user = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: session.get_decoded().get('_auth_user_id')
            )
            if user:
                await sio.save_session(sid, {'user_id': str(user)})
                return True
    except Exception as e:
        print(f"Connection error: {str(e)}")
    return False

@sio.event
async def message(sid, data):
    """Handle incoming chat message"""
    try:
        session = await sio.get_session(sid)
        sender_id = session.get('user_id')
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        
        if not all([sender_id, recipient_id, content]):
            return {'status': 'error', 'message': 'Missing required fields'}
            
        # Save message to database
        message = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: Message.objects.create(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content
            )
        )
        
        # Get room name for these two users
        room = get_room_name(sender_id, recipient_id)
        
        # Get sender's username
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            sender = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: User.objects.get(id=sender_id)
            )
            sender_username = sender.username
        except Exception as e:
            sender_username = 'Unknown'
        
        # Prepare message data
        message_data = {
            'id': str(message.id),
            'sender_id': sender_id,
            'sender_username': sender_username,
            'recipient_id': recipient_id,
            'content': content,
            'timestamp': message.timestamp.isoformat(),
            'is_read': False
        }
        
        # Emit message to the room
        await sio.emit('new_message', message_data, room=room)
        
        # Also send to the sender (in case they're not in the room yet)
        await sio.emit('new_message', message_data, room=sid)
        
        return {'status': 'success', 'message': 'Message sent', 'message_id': str(message.id)}
        
    except Exception as e:
        print(f"Message error: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    

@sio.event
async def join_room(sid, data):
    """Join a chat room"""
    try:
        session = await sio.get_session(sid)
        user_id = session.get('user_id')
        other_user_id = data.get('other_user_id')
        
        if not all([user_id, other_user_id]):
            return {'status': 'error', 'message': 'Missing user IDs'}
        
        room = get_room_name(user_id, other_user_id)
        await sio.enter_room(sid, room)
        return {'status': 'success', 'room': room}
    except Exception as e:
        print(f"Join room error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@sio.event
async def leave_room(sid, data):
    """Leave a chat room"""
    try:
        session = await sio.get_session(sid)
        user_id = session.get('user_id')
        other_user_id = data.get('other_user_id')
        
        if not all([user_id, other_user_id]):
            return {'status': 'error', 'message': 'Missing user IDs'}
        
        room = get_room_name(user_id, other_user_id)
        await sio.leave_room(sid, room)
        return {'status': 'success'}
    except Exception as e:
        print(f"Leave room error: {str(e)}")
        return {'status': 'error', 'message': str(e)}
