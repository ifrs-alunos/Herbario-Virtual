"""Preenche Profile.telegram_username a partir dos vínculos feitos por e-mail.

Sem isto, quem já estava vinculado pelo fluxo antigo fica com o campo vazio: o
/start continua respondendo "já vinculada", mas o primeiro save do perfil
desfaria o vínculo, porque o @ declarado não corresponde mais a conversa nenhuma
(ver telegram_bot/signals.sync_profile_link).
"""

import re

from django.db import migrations

# Cópias locais de propósito: uma migração não pode depender de código do app,
# que muda com o tempo. Espelham accounts/models/profile.py.
USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{5,32}$')


def normalizar(valor):
    if not valor:
        return None

    valor = str(valor).strip()
    valor = re.sub(r'^(https?://)?(t\.me|telegram\.me)/', '', valor, flags=re.IGNORECASE)
    valor = valor.lstrip('@').strip().lower()

    return valor or None


def backfill(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    TelegramUser = apps.get_model('telegram_bot', 'TelegramUser')

    # O campo é unique: um @ já reivindicado por outro perfil não pode ser reusado.
    usados = set(
        Profile.objects.exclude(telegram_username=None)
        .values_list('telegram_username', flat=True)
    )

    conversas = (
        TelegramUser.objects
        .filter(profile__isnull=False)
        .exclude(username='')
        .select_related('profile')
    )

    for conversa in conversas:
        if conversa.profile.telegram_username:
            continue

        username = normalizar(conversa.username)

        # Conversas cujo @ não passa no formato do Telegram ficam de fora: o
        # dono resolve informando o @ no perfil, como qualquer conta nova.
        if username is None or not USERNAME_RE.match(username) or username in usados:
            continue

        # update() e não save(): o model histórico não tem a normalização do save().
        Profile.objects.filter(pk=conversa.profile_id).update(telegram_username=username)
        usados.add(username)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_profile_telegram_username'),
        # A conversa só aponta para um perfil a partir desta migração
        ('telegram_bot', '0003_telegramuser_profile'),
    ]

    operations = [
        # Sem reverso: não há como saber depois quais campos vieram daqui e
        # quais o próprio usuário preencheu.
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
