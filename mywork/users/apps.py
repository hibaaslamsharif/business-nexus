from django.apps import AppConfig
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from django.contrib.auth import get_user_model
        from .models import Profile

        User = get_user_model()

        def create_profile(sender, instance, created, **kwargs):
            if created:
                Profile.objects.get_or_create(user=instance)

        post_save.connect(create_profile, sender=User)
