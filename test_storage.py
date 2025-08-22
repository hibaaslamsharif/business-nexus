#!/usr/bin/env python3

# Quick test to verify storage is working
import sys
import os
sys.path.append('/Users/hibaaslamsharif/Downloads/business nexus intern/mywork')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywork.settings')
import django
django.setup()

from chat.storage import message_storage

# Test adding a message
test_message = {
    'sender_id': 1,
    'receiver_id': 2,
    'message': 'Test message',
    'sender_name': 'Test User',
    'timestamp': '2025-01-22T23:46:00Z',
    'room': 'chat_1_2'
}

print("Adding test message...")
msg_id = message_storage.add_message(test_message)
print(f"Message ID: {msg_id}")

print("\nRetrieving messages for room chat_1_2...")
messages = message_storage.get_messages_for_room('chat_1_2')
print(f"Found messages: {messages}")

print("\nAll messages in storage:")
all_messages = message_storage.get_all_messages()
print(f"Total: {len(all_messages)}")
for msg in all_messages:
    print(f"  - {msg}")
