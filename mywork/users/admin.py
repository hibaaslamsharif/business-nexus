from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Profile, CollaborationRequest

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'startup_name', 'funding_need')
    search_fields = ('user__username', 'startup_name')


@admin.register(CollaborationRequest)
class CollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'investor', 'entrepreneur', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('investor__username', 'entrepreneur__username')
