from django.conf import settings
from django.db import models

from telegram_bot.storage import AIMediaStorage


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


# Subpastas de media-ia/training/. A imagem de treino chega em pending/ e só vai
# para approved/ quando um administrador a aprova e categoriza no painel
# ("Modelos de IA") — inclusive a enviada por outro administrador.
TRAINING_PENDING_DIR = 'training/pending'
TRAINING_APPROVED_DIR = 'training/approved'


def telegram_photo_directory_path(instance, filename):
    """Caminho da imagem dentro de media-ia/: training/pending/ ou test/, conforme o uso escolhido.

    O nome desta função está gravado na migração 0002 — renomeá-la quebra as migrações.
    """

    if instance.purpose == TelegramPhoto.PURPOSE_TRAINING:
        aprovada = instance.review_status == TelegramPhoto.REVIEW_APPROVED
        pasta = TRAINING_APPROVED_DIR if aprovada else TRAINING_PENDING_DIR
        return '{}/{}'.format(pasta, filename)
    return '{}/{}'.format(instance.purpose, filename)


class TelegramPhotoQuerySet(models.QuerySet):

    def pending(self):
        """Imagens recebidas cujo uso (treino ou teste) o usuário ainda não escolheu.

        O image='' deixa de fora os registros anteriores a este fluxo, que já
        têm arquivo (em media/telegram/) mas nenhum uso definido.
        """
        return self.filter(purpose='', image='')

    def awaiting_description(self):
        """Imagens de treino já gravadas cuja descrição o bot ainda espera do usuário"""
        return self.filter(purpose=TelegramPhoto.PURPOSE_TRAINING, awaiting_description=True)

    def awaiting_approval(self):
        """Imagens de treino já gravadas e descritas que esperam a revisão de um administrador.

        Inclui as de antes da revisão existir (gravadas direto em training/): ao
        serem aprovadas, também vão para training/approved/.
        """
        return self.filter(
            purpose=TelegramPhoto.PURPOSE_TRAINING,
            review_status=TelegramPhoto.REVIEW_PENDING,
            awaiting_description=False,
        ).exclude(image='')

    def approved(self):
        """Imagens de treino liberadas por um administrador, em training/approved/"""
        return self.filter(purpose=TelegramPhoto.PURPOSE_TRAINING, review_status=TelegramPhoto.REVIEW_APPROVED)

    def rejected(self):
        """Imagens de treino reprovadas: o registro fica, o arquivo foi apagado"""
        return self.filter(purpose=TelegramPhoto.PURPOSE_TRAINING, review_status=TelegramPhoto.REVIEW_REJECTED)


class TelegramPhoto(models.Model):
    """Imagem enviada por um usuário ao bot do Telegram.

    O registro nasce ao receber a imagem, só com os dados do Telegram. O arquivo
    é baixado depois que o usuário responde se ela serve para treinar ou testar o
    modelo, e vai para media-ia/training/ ou media-ia/test/ — o banco guarda
    apenas o caminho relativo, nunca o binário.
    """

    SOURCE_CHOICES = [
        ('photo', 'Foto'),
        ('document', 'Arquivo'),
    ]

    # Os valores são também os nomes das pastas dentro de media-ia/
    PURPOSE_TRAINING = 'training'
    PURPOSE_TEST = 'test'
    PURPOSE_CHOICES = [
        (PURPOSE_TRAINING, 'Treinamento'),
        (PURPOSE_TEST, 'Teste'),
    ]

    # Decisão sobre uma imagem de treino. Vazio para as de teste e para as que
    # ainda não têm uso definido, que não passam por revisão.
    REVIEW_PENDING = 'pending'
    REVIEW_APPROVED = 'approved'
    REVIEW_REJECTED = 'rejected'
    REVIEW_CHOICES = [
        (REVIEW_PENDING, 'Aguardando revisão'),
        (REVIEW_APPROVED, 'Aprovada'),
        (REVIEW_REJECTED, 'Reprovada'),
    ]

    telegram_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Usuário do Telegram"
    )

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        blank=True,
        db_index=True,
        verbose_name="Uso no modelo",
        help_text="Vazio enquanto o usuário não responde se a imagem é para treinar ou testar."
    )

    # Vazio enquanto o uso não foi escolhido: o download só acontece depois
    image = models.ImageField(
        upload_to=telegram_photo_directory_path,
        storage=AIMediaStorage(),
        blank=True,
        verbose_name="Imagem",
        max_length=500,
        width_field='width',
        height_field='height'
    )

    # Nome original de quem envia como arquivo; fotos comprimidas não têm nome
    file_name = models.CharField(max_length=255, blank=True, verbose_name="Nome do arquivo")

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
    classified_at = models.DateTimeField(null=True, blank=True, verbose_name="Uso escolhido em")

    # Descrição livre que o usuário manda ao bot depois de escolher "treinar"
    # (qual planta, se está saudável, que doença pode ter...). Serve de apoio a
    # quem aprova; a classificação que vale é a de disease/disease_state.
    description = models.TextField(blank=True, verbose_name="Descrição do envio")
    awaiting_description = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Aguardando descrição",
        help_text="Imagem de treino já gravada cuja descrição o bot ainda espera do usuário."
    )
    # Número da imagem no pedido de descrições ("1 - ...", "2 - ..."). O bot cita
    # cada foto com o número dela, para o usuário saber qual é qual.
    description_number = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Número no lote")

    # Categorização feita por quem aprova. A planta é a cultura da doença
    # (disease.culture_disease). SET_NULL: apagar uma doença não apaga a imagem.
    # O estado é um dos itens de disease.states, copiado como texto: renomear o
    # estado na doença depois não altera as imagens já aprovadas.
    disease = models.ForeignKey(
        'disease.Disease',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='telegram_photos',
        verbose_name="Doença"
    )
    disease_state = models.CharField(max_length=60, blank=True, verbose_name="Estado")

    # Só imagens de treino passam por revisão; nas de teste estes campos ficam vazios.
    # A decisão fica sempre registrada: reprovar apaga só o arquivo, e o registro
    # continua com o status, quem decidiu e quando.
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_CHOICES,
        blank=True,
        db_index=True,
        verbose_name="Revisão"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Revisada em")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_telegram_photos',
        verbose_name="Revisada por"
    )

    objects = TelegramPhotoQuerySet.as_manager()

    class Meta:
        verbose_name = "Imagem do Telegram"
        verbose_name_plural = "Imagens do Telegram"
        ordering = ['-received_at']
        permissions = [('approve_telegramphoto', 'Pode aprovar imagens de treino do modelo de IA')]

    def __str__(self):
        return f"Imagem #{self.pk} de {self.telegram_user}"