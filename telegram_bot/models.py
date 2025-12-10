from django.db import models
from django.conf import settings
from django.utils import timezone

class TelegramUser(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_alert_sent = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Usuário do Telegram"
        verbose_name_plural = "Usuários do Telegram"
        ordering = ['-subscribed_at']

    def __str__(self):
        return f"{self.username or self.first_name or 'Usuário'} ({self.chat_id})"

    @classmethod
    def subscribe(cls, chat_id, username="", first_name=""):
        user, created = cls.objects.get_or_create(
            chat_id=chat_id,
            defaults={
                'username': username,
                'first_name': first_name,
                'is_active': True
            }
        )
        
        if not created and not user.is_active:
            user.is_active = True
            user.save()
        
        return user, created

    @classmethod
    def unsubscribe(cls, chat_id):
        try:
            user = cls.objects.get(chat_id=chat_id)
            user.is_active = False
            user.save()
            return True
        except cls.DoesNotExist:
            return False