import json
import socketio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

class SocketIOConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("WebSocket connection established")

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                event = data.get('event')
                
                if event == 'join_room':
                    await self.join_room(data)
                elif event == 'message':
                    await self.handle_message(data)
            except json.JSONDecodeError:
                print("Invalid JSON received")

    async def join_room(self, data):
        user_id = data.get('user_id')
        other_user_id = data.get('other_user_id')
        
        if not all([user_id, other_user_id]):
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Missing user_id or other_user_id'
            }))
            return

        # Create a unique room name for the chat
        room_name = f"chat_{min(int(user_id), int(other_user_id))}_{max(int(user_id), int(other_user_id))}"
        
        # Add to room
        await self.channel_layer.group_add(
            room_name,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'status': 'success',
            'message': f'Joined room {room_name}',
            'room': room_name
        }))

    async def handle_message(self, data):
        message = data.get('content')
        sender_id = data.get('sender_id')
        recipient_id = data.get('recipient_id')
        
        if not all([message, sender_id, recipient_id]):
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Missing required fields'
            }))
            return
        
        # Save message to database
        try:
            sender = await self.get_user(sender_id)
            recipient = await self.get_user(recipient_id)
            
            if not sender or not recipient:
                raise Exception("Invalid sender or recipient")
                
            # Create and save message
            await self.save_message(sender, recipient, message)
            
            # Create room name (same as in join_room)
            room_name = f"chat_{min(int(sender_id), int(recipient_id))}_{max(int(sender_id), int(recipient_id))}"
            
            # Send message to room group
            await self.channel_layer.group_send(
                room_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': str(sender_id),
                    'recipient_id': str(recipient_id),
                    'sender_username': sender.username
                }
            )
            
            await self.send(text_data=json.dumps({
                'status': 'success',
                'message': 'Message sent successfully'
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': str(e)
            }))
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'recipient_id': event['recipient_id'],
            'sender_username': event.get('sender_username', 'Unknown')
        }))
    
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, sender, recipient, content):
        return Message.objects.create(
            sender=sender,
            recipient=recipient,
            content=content
        )

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_user_id = self.scope['url_route']['kwargs']['other_user_id']
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            print(f"WS connect rejected: anonymous user on {self.scope.get('path')}")
            await self.close()
            return
        
        # Create a consistent room name for the two users
        user_ids = sorted([str(self.user.id), str(self.other_user_id)])
        # room_name is plain (e.g. 1_2); group name is prefixed with 'chat_'
        self.room_name = f"{'_'.join(user_ids)}"
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Notify user has joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'system_message',
                'message': f"{self.user.username} has joined the chat",
                'is_system': True
            }
        )
        
        # Send chat history
        await self.send_chat_history()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Notify user has left
            if hasattr(self, 'user') and hasattr(self.user, 'username'):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'system_message',
                        'message': f"{self.user.username} has left the chat",
                        'is_system': True
                    }
                )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message')
            
            if not message:
                return
                
            # Save message to database
            message_id = await self.save_message(
                sender_id=str(self.user.id),
                receiver_id=self.other_user_id,
                content=message,
                room_id=self.room_name
            )
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': str(self.user.id),
                    'sender_username': self.user.username,
                    'timestamp': datetime.utcnow().isoformat(),
                    'message_id': str(message_id) if message_id else None
                }
            )
            
        except Exception as e:
            print(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': str(e),
                'type': 'error'
            }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
            'message_id': event.get('message_id')
        }))
        
    async def system_message(self, event):
        # Send system message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': event['message'],
            'is_system': True
        }))
        
    async def send_chat_history(self):
        """Send chat history to the connected client"""
        try:
            # Get messages from database
            messages = await self.get_chat_history()
            
            # Send each message to the client
            for msg in messages:
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'message': msg['content'],
                    'sender_id': msg['sender_id'],
                    'sender_username': msg.get('sender_username', 'Unknown'),
                    'timestamp': msg['timestamp'].isoformat() if hasattr(msg['timestamp'], 'isoformat') else msg['timestamp'],
                    'message_id': str(msg.get('_id', ''))
                }))
        except Exception as e:
            print(f"Error sending chat history: {str(e)}")
    
    @database_sync_to_async
    def get_chat_history(self):
        """Retrieve chat history from database"""
        from .models import Message
        from django.contrib.auth import get_user_model
        
        try:
            messages = list(Message.objects.filter(
                room_id=self.room_name
            ).order_by('timestamp')[:50])  # Get last 50 messages
            
            # Convert to list of dicts and add sender usernames
            User = get_user_model()
            result = []
            for msg in messages:
                msg_dict = {
                    '_id': str(msg.id),
                    'sender_id': str(msg.sender_id),
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'room_id': msg.room_id
                }
                try:
                    sender = User.objects.get(id=msg.sender_id)
                    msg_dict['sender_username'] = sender.username
                except User.DoesNotExist:
                    msg_dict['sender_username'] = 'Unknown'
                result.append(msg_dict)
            
            return result
            
        except Exception as e:
            print(f"Error getting chat history: {str(e)}")
            return []
    
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content, room_id):
        """Save message to the database"""
        from .models import Message
        from django.utils import timezone
        
        try:
            message = Message.objects.create(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                room_id=room_id,
                timestamp=timezone.now()
            )
            return message.id
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None
