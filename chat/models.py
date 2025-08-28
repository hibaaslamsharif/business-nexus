from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Message(models.Model):
    sender = models.ForeignKey(
        User, 
        related_name='sent_messages', 
        on_delete=models.CASCADE,
        db_index=True
    )
    receiver = models.ForeignKey(
        User, 
        related_name='received_messages', 
        on_delete=models.CASCADE,
        db_index=True
    )
    room_id = models.CharField(max_length=100, db_index=True, help_text='Format: chat_<smaller_user_id>_<larger_user_id>')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']  # Changed to ascending for chat history
        indexes = [
            models.Index(fields=['room_id', 'timestamp']),
        ]

    def __str__(self):
        return f'From {self.sender} to {self.receiver} at {self.timestamp}'
    
    @classmethod
    def get_messages_for_room(cls, room_id, limit=50):
        """Helper method to get messages for a specific room"""
        return cls.objects.filter(room_id=room_id).select_related('sender', 'receiver').order_by('timestamp')[:limit]
    
    @classmethod
    def get_unread_count(cls, user_id, room_id=None):
        """Get count of unread messages for a user"""
        qs = cls.objects.filter(receiver_id=user_id, is_read=False)
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs.count()
    
    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
            return True
        return False


class Presence(models.Model):
    """Tracks user's last seen for presence heuristics."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return f"Presence({self.user_id}) last_seen={self.last_seen}"

    @classmethod
    def heartbeat(cls, user_id):
        obj, _ = cls.objects.update_or_create(user_id=user_id, defaults={'last_seen': timezone.now()})
        return obj
