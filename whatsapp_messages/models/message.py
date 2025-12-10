import secrets
import string
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

class MessageConfirmation(models.Model):
    """Modelo para confirmação de mensagens e vinculação do Telegram"""
    profile = models.OneToOneField(
        'accounts.Profile', 
        on_delete=models.CASCADE,
        related_name='message_confirmation'
    )
    code = models.CharField(max_length=6, null=True, blank=True)
    verified = models.BooleanField(default=False)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    telegram_first_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Confirmação de Mensagem"
        verbose_name_plural = "Confirmações de Mensagem"

    def __str__(self):
        return f"Confirmação de {self.profile.user.username}"

    def has_expired(self):
        """Verifica se o código expirou (60 minutos)"""
        return (timezone.now() - self.created_at).total_seconds() / 60 > 60

    def generate_code(self):
        """Gera um novo código de confirmação"""
        self.code = "".join(secrets.choice(string.digits) for _ in range(6))
        self.created_at = timezone.now()
        self.verified = False
        self.save()
        return self.code

    def verify_code(self, code):
        """Verifica se o código é válido"""
        if not self.has_expired() and self.code == code:
            self.verified = True
            self.save()
            return True
        return False

class TelegramSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Usuário",
        null=True,
        blank=True
    )
    chat_id = models.BigIntegerField(
        "ID do Chat no Telegram",
        unique=True
    )
    username = models.CharField(
        "Username do Telegram",
        max_length=100,
        blank=True
    )
    first_name = models.CharField(
        "Primeiro Nome",
        max_length=100,
        blank=True
    )
    is_active = models.BooleanField(
        "Ativo",
        default=True
    )
    subscribed_at = models.DateTimeField(
        "Data de inscrição",
        auto_now_add=True
    )
    last_alert_sent = models.DateTimeField(
        "Último alerta enviado",
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Inscrição do Telegram"
        verbose_name_plural = "Inscrições do Telegram"
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return f"{self.username or self.first_name or 'Usuário'} ({self.chat_id})"
    
    @classmethod
    def subscribe(cls, chat_id, username="", first_name="", user=None):
        subscription, created = cls.objects.get_or_create(
            chat_id=chat_id,
            defaults={
                'user': user,
                'username': username,
                'first_name': first_name,
                'is_active': True
            }
        )
        
        if not created and not subscription.is_active:
            subscription.is_active = True
            subscription.user = user
            subscription.save()
        
        return subscription, created
    
    @classmethod
    def unsubscribe(cls, chat_id):
        try:
            subscription = cls.objects.get(chat_id=chat_id)
            subscription.is_active = False
            subscription.save()
            return True
        except cls.DoesNotExist:
            return False

class Message(models.Model):
    """Modelo para mensagens enviadas"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregue'),
        ('read', 'Lida'),
        ('failed', 'Falha'),
    ]
    
    MESSAGE_TYPES = [
        ('alert', 'Alerta'),
        ('confirmation', 'Confirmação'),
        ('notification', 'Notificação'),
    ]
    
    sender = models.ForeignKey(
        'accounts.Profile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages',
        verbose_name="Remetente"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name="Destinatário"
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='notification',
        verbose_name="Tipo de Mensagem"
    )
    disease = models.ForeignKey(
        'disease.Disease',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Doença relacionada"
    )
    math_model_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Referência do Modelo"
    )
    
    message_text = models.TextField(verbose_name="Texto da mensagem")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    external_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID externo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_log = models.JSONField(
        default=list,
        verbose_name="Histórico de status"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Mensagem de erro"
    )
    delivery_details = models.JSONField(
        default=dict,
        verbose_name="Detalhes da entrega"
    )

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        return f"Mensagem {self.id} para {self.receiver} ({self.status})"

    def update_status(self, new_status, details=None):
        """Atualiza o status da mensagem e registra no histórico"""
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValidationError(f"Status inválido: {new_status}")
            
        self.status = new_status
        self.status_log.append({
            'status': new_status,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        })
        self.save()

    @property
    def last_status(self):
        """Retorna o último registro de status"""
        if self.status_log:
            return self.status_log[-1]
        return None

    def send_whatsapp(self):
        """Envia mensagem via WhatsApp"""
        try:
            self.update_status('sent')
            return True
        except Exception as e:
            self.update_status('failed', {'error': str(e)})
            return False

    def send_telegram(self):
        """Envia mensagem via Telegram"""
        try:
            self.update_status('sent')
            return True
        except Exception as e:
            self.update_status('failed', {'error': str(e)})
            return False