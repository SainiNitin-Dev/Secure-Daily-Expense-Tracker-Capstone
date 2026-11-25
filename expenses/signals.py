from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

from .models import FailedLoginAttempt


@receiver(user_login_failed)
def record_failed_login(sender, credentials, **kwargs):
    username = str(credentials.get("username") or "")
    FailedLoginAttempt.objects.create(username=username[:150])
