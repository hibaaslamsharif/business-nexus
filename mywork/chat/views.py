from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from pymongo import MongoClient
import json

# MongoDB connection - same as in api_views.py
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Test connection
    db = client['business_nexus']
    messages_collection = db['chat_messages']
    MONGODB_AVAILABLE = True
    print("MongoDB connected successfully in chat views")
except Exception as e:
    print(f"MongoDB connection failed in chat views: {e}")
    MONGODB_AVAILABLE = False
    messages_collection = None

class ChatHistoryView(APIView):
    """API to get chat history between two users"""
    
    def get(self, request, user_id):
        try:
            current_user_id = request.GET.get('current_user', 1)
            print(f"Loading chat history between users {current_user_id} and {user_id}")
            
            if not MONGODB_AVAILABLE:
                print("MongoDB not available, using fallback storage")
                from .storage import message_storage
                
                room_name = f"chat_{min(int(current_user_id), int(user_id))}_{max(int(current_user_id), int(user_id))}"
                messages = message_storage.get_messages_for_room(room_name)
                
                return Response({
                    'success': True,
                    'messages': messages,
                    'room': room_name
                })
            
            # Create consistent room name
            room_name = f"chat_{min(int(current_user_id), int(user_id))}_{max(int(current_user_id), int(user_id))}"
            print(f"Looking for messages in room: {room_name}")
            
            # Query messages for this room
            messages = list(messages_collection.find(
                {'room': room_name}
            ).sort('timestamp', 1))
            
            print(f"Found {len(messages)} messages")
            
            # Convert ObjectId to string and format timestamp
            for message in messages:
                message['_id'] = str(message['_id'])
                if isinstance(message['timestamp'], datetime):
                    message['timestamp'] = message['timestamp'].isoformat()
            
            return Response({
                'success': True,
                'messages': messages,
                'room': room_name
            })
            
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
