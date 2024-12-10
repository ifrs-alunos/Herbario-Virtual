import secrets
import string

from django.db import models
from django.utils import timezone

from accounts.models import Profile

CODE_LENGTH = 6
CODE_EXPIRATION_TIME = 60  # minutes


class MessageConfirmation(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    code = models.CharField(max_length=CODE_LENGTH, null=True, blank=True)
    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def has_expired(self):
        return (
                timezone.now() - self.created_at
        ).total_seconds() / 60 > CODE_EXPIRATION_TIME

    @property
    def phone_number(self):
        return self.profile.phone

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = "".join(
                secrets.choice(string.digits) for _ in range(CODE_LENGTH)
            )
        super().save(*args, **kwargs)
