from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from pymongo import MongoClient
import os

# MongoDB connection - with error handling
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Test connection
    db = client['business_nexus']
    messages_collection = db['chat_messages']
    MONGODB_AVAILABLE = True
    print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    MONGODB_AVAILABLE = False
    messages_collection = None

class SendMessageView(APIView):
    def post(self, request):
        try:
            data = request.data
            print(f"Received message data: {data}")
            
            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            message_text = data.get('message')
            sender_name = data.get('sender_name')
            
            if not all([sender_id, receiver_id, message_text]):
                print("Missing required fields")
                return Response({
                    'success': False,
                    'error': 'Missing required fields'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If MongoDB is not available, use fallback storage
            if not MONGODB_AVAILABLE:
                print("MongoDB not available, using fallback storage")
                from .storage import message_storage
                
                message_obj = {
                    'sender_id': int(sender_id),
                    'receiver_id': int(receiver_id),
                    'message': message_text,
                    'sender_name': sender_name or f'User {sender_id}',
                    'timestamp': datetime.utcnow().isoformat(),
                    'room': f"chat_{min(int(sender_id), int(receiver_id))}_{max(int(sender_id), int(receiver_id))}"
                }
                
                message_id = message_storage.add_message(message_obj)
                
                return Response({
                    'success': True,
                    'message': 'Message sent successfully (fallback)',
                    'message_id': str(message_id)
                })
            
            # Create message document
            message_doc = {
                'sender_id': int(sender_id),
                'receiver_id': int(receiver_id),
                'message': message_text,
                'sender_name': sender_name or f'User {sender_id}',
                'timestamp': datetime.utcnow(),
                'room': f"chat_{min(int(sender_id), int(receiver_id))}_{max(int(sender_id), int(receiver_id))}"
            }
            
            print(f"Saving message: {message_doc}")
            
            # Save to MongoDB
            result = messages_collection.insert_one(message_doc)
            print(f"Message saved with ID: {result.inserted_id}")
            
            return Response({
                'success': True,
                'message': 'Message sent successfully',
                'message_id': str(result.inserted_id)
            })
            
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
