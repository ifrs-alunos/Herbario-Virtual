import secrets
import string
import urllib.parse

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


class WhatsappNumber(models.Model):
    """
    Modelo de uso interno, apenas um número pode existir simultaneamente, usado no processador de contexto
    """
    number = models.CharField(max_length=20)

    def get_whatsapp_url(self, message):
        message = urllib.parse.quote(message)
        return f'https://wa.me/{self.number}?text={message}'

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if WhatsappNumber.objects.count() > 0:
            raise ValidationError("Já existe um número de WhatsApp cadastrado")
        else:
            super(WhatsappNumber, self).save(*args, **kwargs)


CODE_LENGTH = 6
CODE_EXPIRATION_TIME = 60  # minutes


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=CODE_LENGTH, null=True, blank=True)
    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


@receiver(pre_save, sender=VerificationCode)
def generate_code(sender, instance: VerificationCode, **_kwargs):
    if not instance.code:
        instance.code = ''.join(secrets.choice(string.digits) for _ in range(CODE_LENGTH))
        instance.save()
