import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from datetime import datetime
import pymongo
from bson import ObjectId
from django.conf import settings

User = get_user_model()

# MongoDB connection
try:
    client = pymongo.MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_NAME]
    messages_collection = db['chat_messages']
    # Create index for faster queries
    messages_collection.create_index([('room_id', 1), ('timestamp', 1)])
    MONGODB_AVAILABLE = True
except:
    MONGODB_AVAILABLE = False

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
            
        self.other_user_id = self.scope['url_route']['kwargs']['other_user_id']
        self.room_name = self._get_room_name(self.user.id, self.other_user_id)
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    def _get_room_name(self, user1_id, user2_id):
        """Generate a consistent room name for any pair of users"""
        return f"{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            
            # Save message to database
            await self.save_message(
                sender_id=str(self.user.id),
                receiver_id=self.other_user_id,
                message=message,
                room_id=self.room_name
            )
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': str(self.user.id),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            print(f"Error in receive: {str(e)}")

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, room_id):
        if not MONGODB_AVAILABLE:
            return None
            
        message_data = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message,
            'room_id': room_id,
            'timestamp': datetime.utcnow(),
            'read': False
        }
        return messages_collection.insert_one(message_data)
