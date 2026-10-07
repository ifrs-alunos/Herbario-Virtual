"""Mantém os vínculos do Telegram em dia com o que está no perfil do Labfito.

Fica em telegram_bot (e não em accounts) para preservar a direção da
dependência: este app já importa accounts, o contrário não.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from accounts.models import Profile
from telegram_bot import messages
from telegram_bot.models import TelegramUser
from telegram_bot.services import send_telegram_message

logger = logging.getLogger(__name__)


def sync_profile_link(profile, notify=True):
    """Reflete Profile.telegram_username nos TelegramUser.

    Desfaz o vínculo de conversas que não correspondem mais ao @ declarado
    (troca ou remoção do campo) e reivindica a conversa de quem já havia
    enviado /start com aquele @ — é o que permite o vínculo acontecer no
    momento em que o usuário salva o perfil, sem precisar voltar ao bot.

    Retorna o TelegramUser vinculado agora, ou None.
    """

    declarado = profile.telegram_username  # já normalizado por Profile.save()

    # Vínculos obsoletos: o @ mudou ou foi apagado no perfil.
    obsoletos = TelegramUser.objects.filter(profile=profile)
    if declarado:
        obsoletos = obsoletos.exclude(username__iexact=declarado)
    obsoletos.update(profile=None, linked_at=None)

    if not declarado:
        return None

    # iexact: registros criados antes da normalização podem ter maiúsculas.
    telegram_user = TelegramUser.objects.filter(username__iexact=declarado).first()

    if telegram_user is None or telegram_user.profile_id == profile.pk:
        return None

    if telegram_user.profile_id is not None:
        # A conversa pertence a outra conta; quem decide é o admin.
        logger.warning(
            "Chat %s tem o @%s mas já está vinculado a outro perfil (%s)",
            telegram_user.chat_id, declarado, telegram_user.profile_id
        )
        return None

    telegram_user.profile = profile
    telegram_user.linked_at = timezone.now()
    telegram_user.save(update_fields=['profile', 'linked_at'])

    if notify:
        send_telegram_message(
            telegram_user.chat_id,
            messages.VINCULO_OK.format(
                profile_name=profile.name or profile.user.username,
                username=profile.user.username,
            )
        )

    return telegram_user


@receiver(post_save, sender=Profile)
def sync_profile_link_on_save(sender, instance, **kwargs):
    """Roda a cada save de Profile — inclusive os indiretos, via accounts.signals.

    on_commit: se a transação do formulário falhar depois, nada de vínculo nem
    de mensagem enviada. A função é idempotente e só notifica quando o vínculo
    é de fato criado, então os saves repetidos não geram mensagens duplicadas.
    """

    def _sync():
        try:
            sync_profile_link(instance)
        except Exception:
            # Um perfil não pode deixar de ser salvo porque o Telegram falhou.
            logger.exception("Falha ao sincronizar o vínculo do Telegram do perfil %s", instance.pk)

    transaction.on_commit(_sync)
