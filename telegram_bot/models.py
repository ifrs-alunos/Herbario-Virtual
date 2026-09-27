from django.db import models
from django.utils import timezone


class TelegramUserQuerySet(models.QuerySet):

    def linked(self):
        """Conversas já vinculadas a uma conta do sistema"""
        return self.filter(profile__isnull=False)

    def receiving_alerts(self):
        """Ponto único de verdade sobre quem recebe alertas.

        Hoje: inscrição ativa + conta do sistema vinculada + conta ativa.
"""
        return self.filter(
            is_active=True,
            profile__isnull=False,
            profile__user__is_active=True,
        ).select_related('profile', 'profile__user')


class TelegramUser(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_alert_sent = models.DateTimeField(null=True, blank=True)

    # SET_NULL e não CASCADE: apagar um Profile (ProfileDeleteView existe no
    # painel) não pode levar junto o TelegramUser, senão o CASCADE de
    # TelegramPhoto destruiria o histórico de imagens recebidas.
    profile = models.OneToOneField(
        'accounts.Profile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='telegram_user',
        verbose_name="Conta vinculada"
    )
    linked_at = models.DateTimeField(null=True, blank=True, verbose_name="Vinculado em")

    objects = TelegramUserQuerySet.as_manager()

    class Meta:
        verbose_name = "Usuário do Telegram"
        verbose_name_plural = "Usuários do Telegram"
        ordering = ['-subscribed_at']

    def __str__(self):
        return f"{self.username or self.first_name or 'Usuário'} ({self.chat_id})"

    @property
    def is_linked(self):
        return self.profile_id is not None

    @property
    def receives_alerts(self):
        return bool(self.is_active and self.profile_id)

    @classmethod
    def unsubscribe(cls, chat_id):
        try:
            user = cls.objects.get(chat_id=chat_id)
            user.is_active = False
            user.save()
            return True
        except cls.DoesNotExist:
            return False


def telegram_photo_directory_path(instance, filename):
    """Esta função retorna o diretório onde as imagens recebidas via Telegram devem ser armazenadas"""

    return 'telegram/{}/{:%Y/%m}/{}'.format(instance.telegram_user.chat_id, timezone.now(), filename)


class TelegramPhoto(models.Model):
    """Imagem enviada por um usuário ao bot do Telegram"""

    SOURCE_CHOICES = [
        ('photo', 'Foto'),
        ('document', 'Arquivo'),
    ]

    telegram_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Usuário do Telegram"
    )

    image = models.ImageField(
        upload_to=telegram_photo_directory_path,
        verbose_name="Imagem",
        max_length=500,
        width_field='width',
        height_field='height'
    )

    width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    # Identificadores do arquivo na API do Telegram
    file_id = models.CharField(max_length=200, blank=True, verbose_name="File ID")
    file_unique_id = models.CharField(max_length=200, blank=True, db_index=True, verbose_name="File Unique ID")
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tamanho (bytes)")

    caption = models.TextField(blank=True, verbose_name="Legenda")
    telegram_message_id = models.BigIntegerField(null=True, blank=True, verbose_name="ID da mensagem")

    # Fotos enviadas em álbum compartilham o mesmo media_group_id
    media_group_id = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="ID do álbum")

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='photo',
        verbose_name="Origem"
    )

    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Recebida em")

    class Meta:
        verbose_name = "Imagem do Telegram"
        verbose_name_plural = "Imagens do Telegram"
        ordering = ['-received_at']

    def __str__(self):
        return f"Imagem #{self.pk} de {self.telegram_user}"