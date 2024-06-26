import secrets
import string

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from accounts.models import Profile

CODE_LENGTH = 6
CODE_EXPIRATION_TIME = 60  # minutes


class MessageConfirmation(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    code = models.CharField(max_length=CODE_LENGTH, null=True, blank=True)
    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


@receiver(pre_save, sender=MessageConfirmation)
def generate_code(_sender, instance: MessageConfirmation, **_kwargs):
    if not instance.code:
        instance.code = "".join(
            secrets.choice(string.digits) for _ in range(CODE_LENGTH)
        )
        instance.save()
