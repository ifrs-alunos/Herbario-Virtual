from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="Usuário"
    )
    name = models.CharField(max_length=200, verbose_name="Nome completo")
    institution = models.CharField(max_length=150, verbose_name="Instituição")
    role = models.CharField(max_length=100, verbose_name="Cargo")
    phone = models.CharField(
        max_length=11, 
        verbose_name="Telefone", 
        unique=True, 
        null=True,
        blank=True
    )
    whatsapp_enabled = models.BooleanField(
        default=False,
        verbose_name="Receber alertas por WhatsApp"
    )
    whatsapp_verified = models.BooleanField(
        default=False, 
        verbose_name="WhatsApp Verificado"
    )
    whatsapp_opt_in = models.BooleanField(
        default=False, 
        verbose_name="Receber Alertas no WhatsApp"
    )
    cpf = models.CharField(max_length=11, verbose_name="CPF")
    rg = models.CharField(max_length=10, verbose_name="RG")
    alerts_for_diseases = models.ManyToManyField(
        "disease.Disease", 
        blank=True,
        verbose_name="Doenças para alerta"
    )
    get_messages = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def send_alert(self, disease):
        """Envia alerta para o usuário"""
        if hasattr(self, 'messageconfirmation'):
            from whatsapp_messages.functions import send_telegram_message
            send_telegram_message(
                self.messageconfirmation.telegram_chat_id, 
                f"Alerta de doença: {disease.name_disease}"
            )

    def can_send_solicitation(self):
        """Verifica se pode enviar nova solicitação"""
        from .solicitation import Solicitation  # Importação local
        return not self.user.solicitations.filter(
            status__in=[Solicitation.Status.SENT, Solicitation.Status.ACCEPTED]
        ).exists()

    def can_get_messages(self):
        """Ativa recebimento de mensagens"""
        self.get_messages = True
        self.save()

    @classmethod
    def get_profile(cls, user):
        """Obtém ou cria perfil para o usuário"""
        profile, created = cls.objects.get_or_create(user=user)
        return profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria perfil automaticamente para novo usuário"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva perfil quando usuário é salvo"""
    if hasattr(instance, 'profile'):
        instance.profile.save()