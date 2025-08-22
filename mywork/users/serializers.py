from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile, CollaborationRequest


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'user', 'bio',
            'startup_name', 'startup_description', 'funding_need', 'pitch_deck_url',
            'investment_interests', 'portfolio_companies',
        ]


class CollaborationRequestSerializer(serializers.ModelSerializer):
    investor = UserSerializer(read_only=True)
    entrepreneur = UserSerializer(read_only=True)

    class Meta:
        model = CollaborationRequest
        fields = ['id', 'investor', 'entrepreneur', 'status', 'message', 'created_at', 'updated_at']

