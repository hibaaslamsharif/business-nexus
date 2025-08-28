from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    ROLE_CHOICES = [
        ('investor', 'Investor'),
        ('entrepreneur', 'Entrepreneur'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)

    # Entrepreneur-specific
    startup_name = models.CharField(max_length=255, blank=True)
    startup_description = models.TextField(blank=True)
    funding_need = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pitch_deck_url = models.URLField(blank=True)

    # Investor-specific
    investment_interests = models.TextField(blank=True)
    portfolio_companies = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Profile({self.user.username})"


class ProfileView(models.Model):
    """Track unique views of a user's profile by another authenticated user."""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profiles_viewed')
    viewed_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ('profile', 'viewer')
        ordering = ['-viewed_at']

    def __str__(self) -> str:
        return f"{self.viewer.username} viewed {self.profile.user.username}"


class CollaborationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        ACCEPTED = 'Accepted', 'Accepted'
        REJECTED = 'Rejected', 'Rejected'

    investor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    entrepreneur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True)
    # Track who initiated the request so we can show inbox/outbox correctly
    initiated_by = models.CharField(
        max_length=20,
        choices=(('investor', 'Investor'), ('entrepreneur', 'Entrepreneur')),
        default='investor'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Request({self.investor.username} -> {self.entrepreneur.username}, {self.status})"
