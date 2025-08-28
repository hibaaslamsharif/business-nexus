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
    view_count = serializers.SerializerMethodField()
    last_viewed_at = serializers.SerializerMethodField()
    recent_viewers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user', 'bio',
            'startup_name', 'startup_description', 'funding_need', 'pitch_deck_url',
            'investment_interests', 'portfolio_companies',
            'view_count', 'last_viewed_at', 'recent_viewers'
        ]

    def get_view_count(self, obj):
        try:
            return obj.views.count()
        except Exception:
            return 0

    def get_last_viewed_at(self, obj):
        try:
            last = obj.views.order_by('-viewed_at').first()
            return last.viewed_at if last else None
        except Exception:
            return None

    def get_recent_viewers(self, obj):
        try:
            qs = obj.views.select_related('viewer').order_by('-viewed_at')[:10]
            return [
                {
                    'id': v.viewer.id,
                    'username': v.viewer.username,
                    'viewed_at': v.viewed_at,
                }
                for v in qs
            ]
        except Exception:
            return []


class CollaborationRequestSerializer(serializers.ModelSerializer):
    investor = UserSerializer(read_only=True)
    entrepreneur = UserSerializer(read_only=True)

    class Meta:
        model = CollaborationRequest
    fields = ['id', 'investor', 'entrepreneur', 'status', 'message', 'initiated_by', 'created_at', 'updated_at']

