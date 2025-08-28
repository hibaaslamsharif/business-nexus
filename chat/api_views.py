from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
import os
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .storage import message_storage
from .models import Message, Presence
from django.db.models import Count

# Use in-memory storage if MongoDB is not available
MONGODB_AVAILABLE = hasattr(settings, 'MONGO_DB') and settings.MONGO_DB is not None
messages_collection = None

if MONGODB_AVAILABLE:
    try:
        messages_collection = settings.MONGO_DB['chat_messages']
        print("MongoDB connected successfully")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        MONGODB_AVAILABLE = False
        messages_collection = None
else:
    # We always store messages in SQLite as the source of truth
    print("Running in SQLite-only mode. Chat history will persist in SQLite.")

class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Heartbeat for the sender
            try:
                Presence.heartbeat(request.user.id)
            except Exception:
                pass
            data = request.data
            print(f"Received message data: {data}")
            
            recipient_id = data.get('recipient_id')
            content = data.get('content')
            
            if not all([recipient_id, content]):
                return Response(
                    {'success': False, 'error': 'Missing required fields'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get recipient user
            User = get_user_model()
            try:
                recipient = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Recipient not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Disallow sending messages to self to avoid chat_X_X rooms
            try:
                if int(recipient_id) == int(request.user.id):
                    return Response(
                        {
                            'success': False,
                            'error': 'Cannot send a message to yourself. Please select a different user.'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception:
                pass
            
            # Create room name (sorted to ensure consistency)
            room_name = f"chat_{min(int(request.user.id), int(recipient_id))}_{max(int(request.user.id), int(recipient_id))}"
            
            message_data = {
                'sender_id': str(request.user.id),
                'recipient_id': str(recipient_id),
                'content': content,
                'sender_username': request.user.username,
                'room': room_name,
                'timestamp': datetime.utcnow()
            }
            
            # Store in MongoDB if available
            if MONGODB_AVAILABLE and messages_collection is not None:
                try:
                    result = messages_collection.insert_one(message_data)
                    message_data['_id'] = str(result.inserted_id)
                    print(f"Message stored in MongoDB with ID: {message_data['_id']}")
                except Exception as e:
                    print(f"Error storing message in MongoDB: {e}")
            
            # Always store in local storage as fallback
            try:
                # Convert datetime to string for JSON serialization
                storage_data = message_data.copy()
                storage_data['timestamp'] = storage_data['timestamp'].isoformat()
                message_storage.add_message(storage_data)
                print("Message stored in local storage")
                
                # Also store in SQL for reliability
                try:
                    Message.objects.create(
                        sender_id=request.user.id,
                        receiver_id=recipient_id,
                        content=content,
                        room_id=room_name
                    )
                    print("Message stored in SQL")
                except Exception as e:
                    print(f"Error storing message in SQL: {e}")
                
                # Return the message with the same format as MongoDB
                message_data['_id'] = f"local_{len(message_storage.get_all_messages())}"
                
                return Response({
                    'success': True, 
                    'message': {
                        '_id': message_data['_id'],
                        'sender_id': str(message_data['sender_id']),
                        'content': message_data['content'],
                        'timestamp': message_data['timestamp'].isoformat(),
                        'room': message_data['room']
                    }
                })
                
            except Exception as e:
                print(f"Error storing message: {e}")
                return Response(
                    {'success': False, 'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            print(f"Error in SendMessageView: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            # Heartbeat for the viewer
            try:
                Presence.heartbeat(request.user.id)
            except Exception:
                pass
            # Get the other user
            User = get_user_model()
            try:
                other_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create room name (sorted to ensure consistency)
            room_name = f"chat_{min(int(request.user.id), int(user_id))}_{max(int(request.user.id), int(user_id))}"
            
            messages = []

            # 1) Prefer persistent SQLite as the source of truth
            try:
                sql_messages = list(
                    Message.objects.filter(room_id=room_name).order_by('timestamp')
                )
                for m in sql_messages:
                    messages.append({
                        'id': str(m.id),
                        'sender_id': str(m.sender_id),
                        'content': m.content,
                        'timestamp': m.timestamp.isoformat(),
                        'is_me': str(m.sender_id) == str(request.user.id)
                    })
                # print(f"Found {len(messages)} messages in SQL")
            except Exception as e:
                print(f"Error fetching messages from SQL: {e}")

            # 2) If SQL has nothing (e.g., older data path), optionally try Mongo
            if not messages and MONGODB_AVAILABLE and messages_collection is not None:
                try:
                    mongo_messages = messages_collection.find({'room': room_name}).sort('timestamp', 1)
                    for msg in mongo_messages:
                        messages.append({
                            'id': str(msg['_id']),
                            'sender_id': str(msg['sender_id']),
                            'content': msg['content'],
                            'timestamp': msg['timestamp'].isoformat(),
                            'is_me': msg['sender_id'] == str(request.user.id)
                        })
                    # print(f"Found {len(messages)} messages in MongoDB")
                except Exception as e:
                    print(f"Error fetching from MongoDB: {e}")

            # 3) Finally, fall back to in-memory local storage (ephemeral)
            if not messages:
                local_messages = message_storage.get_messages_for_room(room_name)
                for msg in local_messages:
                    messages.append({
                        'id': msg.get('_id', ''),
                        'sender_id': str(msg.get('sender_id', '')),
                        'content': msg.get('content', ''),
                        'timestamp': msg.get('timestamp', ''),
                        'is_me': msg.get('sender_id') == str(request.user.id)
                    })
                # print(f"Found {len(messages)} messages in local storage")
            
            return Response({
                'success': True,
                'messages': messages,
                'current_user_id': str(request.user.id),
                'other_user': {
                    'id': str(other_user.id),
                    'username': other_user.username,
                    'email': other_user.email
                }
            })
            
        except Exception as e:
            print(f"Error in ChatHistoryView: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnreadCountView(APIView):
    """Return total unread message count for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Heartbeat on polling
            try:
                Presence.heartbeat(request.user.id)
            except Exception:
                pass
            total_unread = Message.objects.filter(receiver_id=request.user.id, is_read=False).count()
            return Response({'success': True, 'unread': total_unread})
        except Exception as e:
            # Fail-safe: do not 500 on unread polling; return a safe default and log the error
            try:
                print(f"Error in UnreadCountView: {e}")
            except Exception:
                pass
            return Response({'success': False, 'unread': 0, 'error': str(e)})


class MarkConversationReadView(APIView):
    """Mark messages in a specific conversation as read for the current user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            other_user_id = request.data.get('other_user_id')
            if not other_user_id:
                return Response({'success': False, 'error': 'other_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                other_id_int = int(other_user_id)
            except Exception:
                return Response({'success': False, 'error': 'Invalid other_user_id'}, status=status.HTTP_400_BAD_REQUEST)

            room_name = f"chat_{min(int(request.user.id), other_id_int)}_{max(int(request.user.id), other_id_int)}"
            updated = Message.objects.filter(room_id=room_name, receiver_id=request.user.id, is_read=False).update(is_read=True)
            remaining = Message.objects.filter(receiver_id=request.user.id, is_read=False).count()
            return Response({'success': True, 'marked': updated, 'remaining_unread': remaining})
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PresenceView(APIView):
    """Heuristic presence: user considered online if they sent any message in the last 3 minutes."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            other_user_id = request.query_params.get('user_id')
            if not other_user_id:
                return Response({'success': False, 'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                other_id_int = int(other_user_id)
            except Exception:
                return Response({'success': False, 'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)

            # Prefer Presence heartbeat. Consider online if active in last 2 minutes.
            threshold = timezone.now() - timedelta(minutes=2)
            pres = Presence.objects.filter(user_id=other_id_int).first()
            if pres:
                online = pres.last_seen >= threshold
                last_active = pres.last_seen.isoformat()
            else:
                # Fallback: last message sent within 3 minutes
                window = timezone.now() - timedelta(minutes=3)
                last_msg = (
                    Message.objects
                    .filter(sender_id=other_id_int)
                    .order_by('-timestamp')
                    .first()
                )
                online = bool(last_msg and last_msg.timestamp >= window)
                last_active = last_msg.timestamp.isoformat() if last_msg else None
            return Response({'success': True, 'online': online, 'last_active': last_active})
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnreadByUserView(APIView):
    """Return unread counts grouped by sender for the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            try:
                Presence.heartbeat(request.user.id)
            except Exception:
                pass
            rows = (
                Message.objects
                .filter(receiver_id=request.user.id, is_read=False)
                .values('sender_id')
                .annotate(count=Count('id'))
            )
            data = {str(r['sender_id']): r['count'] for r in rows}
            total = sum(data.values())
            return Response({'success': True, 'by_user': data, 'total': total})
        except Exception as e:
            try:
                print(f"Error in UnreadByUserView: {e}")
            except Exception:
                pass
            return Response({'success': False, 'by_user': {}, 'total': 0, 'error': str(e)})
