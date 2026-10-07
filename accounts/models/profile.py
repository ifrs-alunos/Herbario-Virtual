import re

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# 5 a 32 caracteres, letras/números/underscore — a regra do próprio Telegram.
TELEGRAM_USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{5,32}$')


def normalize_telegram_username(value):
    """Reduz o que o usuário digitou à forma canônica do @ do Telegram.

    '@Fulano', 'https://t.me/Fulano' e ' Fulano ' viram todos 'fulano'. Vazio
    vira None — o campo é unique, e só NULL pode se repetir entre os perfis.

    Guardar sempre em minúsculas é o que faz o unique do banco valer como
    comparação case-insensitive: o Telegram não distingue @Fulano de @fulano.
    """

    if not value:
        return None

    value = str(value).strip()

    # Aceita o link do perfil, que é o que o app do Telegram copia
    value = re.sub(r'^(https?://)?(t\.me|telegram\.me)/', '', value, flags=re.IGNORECASE)
    value = value.lstrip('@').strip()

    return value.lower() or None


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
    # Chave do vínculo com o bot: o /start compara este valor com o @ que a API
    # do Telegram informa. Quem declara o vínculo é o dono da conta do Labfito,
    # e não quem chega no bot. Ver telegram_bot/services.link_by_telegram_username().
    telegram_username = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Usuário do Telegram",
        help_text=("Seu @ no Telegram, sem o @. Opcional — necessário apenas "
                   "para receber os alertas pelo bot.")
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

    def save(self, *args, **kwargs):
        # Normaliza aqui, e não só no formulário, para que admin, shell e bot
        # gravem sempre a mesma forma canônica — é dela que o unique depende.
        self.telegram_username = normalize_telegram_username(self.telegram_username)
        super().save(*args, **kwargs)

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

# Os signals que criam/salvam o Profile ficam em accounts/signals.py.
# Declará-los aqui também conectava dois receivers extras em post_save, e o
# Profile.objects.create() deles colidia com o OneToOneField no cadastro.