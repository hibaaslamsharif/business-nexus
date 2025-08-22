# Simple in-memory storage for chat messages
# This will persist across requests within the same Django process

class MessageStorage:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageStorage, cls).__new__(cls)
            cls._instance._messages = []
        return cls._instance
    
    def add_message(self, message_data):
        """Add a message to storage"""
        message_data['_id'] = len(self._messages) + 1
        self._messages.append(message_data)
        print(f"Message added to storage: {message_data}")
        print(f"Total messages in storage: {len(self._messages)}")
        return message_data['_id']
    
    def get_messages_for_room(self, room_name):
        """Get all messages for a specific room"""
        messages = [msg for msg in self._messages if msg.get('room') == room_name]
        print(f"Retrieved {len(messages)} messages for room {room_name} from total {len(self._messages)}")
        print(f"All rooms in storage: {list(set(msg.get('room') for msg in self._messages))}")
        return messages
    
    def get_all_messages(self):
        """Get all messages"""
        print(f"Total messages in storage: {len(self._messages)}")
        return self._messages

# Global instance
message_storage = MessageStorage()
