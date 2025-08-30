from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.conf import settings
import json

# Optional MongoDB connection – only if enabled in settings
MONGODB_AVAILABLE = False
messages_collection = None
if getattr(settings, 'USE_MONGO', False):
    try:
        from pymongo import MongoClient
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

def simple_chat_view(request, user_id):
    """Simple chat interface view"""
    recipient = get_object_or_404(get_user_model(), id=user_id)

    # Do not require Django session; let frontend fetch messages via REST using JWT.
    # Provide minimal context only.
    context = {
        'recipient': recipient,
        'messages': [],
        'MONGODB_AVAILABLE': MONGODB_AVAILABLE,
        'current_user_id': request.user.id if request.user.is_authenticated else ''
    }
    return render(request, 'chat/simple_chat.html', context)


class ChatHistoryView(APIView):
    """API to get chat history between two users"""
    
    def get(self, request, user_id):
        try:
            current_user_id = request.GET.get('current_user', 1)
            print(f"Loading chat history between users {current_user_id} and {user_id}")
            
            if not MONGODB_AVAILABLE:
                print("MongoDB not available, using fallback storage")
                from .storage import message_storage
            # Create consistent room name
            room_name = f"chat_{min(int(request.user.id), int(user_id))}_{max(int(request.user.id), int(user_id))}"
            
            messages = []
            
            # Try to get messages from MongoDB first if available
            if MONGODB_AVAILABLE and messages_collection:
                try:
                    mongo_messages = list(messages_collection.find({
                        'room': room_name
                    }).sort('timestamp', 1))
                    
                    # Convert ObjectId to string for JSON serialization
                    for msg in mongo_messages:
                        msg['_id'] = str(msg['_id'])
                        if 'timestamp' in msg and hasattr(msg['timestamp'], 'isoformat'):
                            msg['timestamp'] = msg['timestamp'].isoformat()
                    messages.extend(mongo_messages)
                except Exception as e:
                    print(f"Error fetching from MongoDB: {e}")
            
            # Always include messages from local storage
            from .storage import message_storage
            local_messages = message_storage.get_messages_for_room(room_name)
            
            # Add local messages that aren't already in the messages list
            local_message_ids = {msg['_id'] for msg in messages}
            for msg in local_messages:
                if msg.get('_id') not in local_message_ids:
                    messages.append(msg)
            
            # Sort all messages by timestamp
            messages.sort(key=lambda x: x.get('timestamp', ''))
            
            return Response({
                'success': True,
                'messages': messages
            })
            
        except Exception as e:
            print(f"Error in ChatHistoryView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
