"""Camada síncrona do bot do Telegram: imagens, vínculo de contas e envio.

Fica separada dos handlers do python-telegram-bot para poder ser testada e
reutilizada sem depender do loop de eventos nem da API do Telegram.
"""

from collections import namedtuple
from io import BytesIO

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Profile, normalize_telegram_username
from telegram_bot.models import TelegramUser, TelegramPhoto

# Limite de download do método getFile da Bot API
MAX_TELEGRAM_FILE_SIZE = 20 * 1024 * 1024


def save_incoming_photo(chat_id, image_bytes, filename, username="", first_name="",
                        file_id="", file_unique_id="", file_size=None, caption="",
                        telegram_message_id=None, media_group_id="", source='photo'):
    """Salva uma imagem recebida via Telegram e retorna o registro criado.

    Levanta ValueError se os bytes não formarem uma imagem válida.
    """

    if not image_bytes:
        raise ValueError("Nenhum dado de imagem recebido")

    # O ImageField só valida o conteúdo em formulários, então a verificação é feita aqui
    try:
        Image.open(BytesIO(image_bytes)).verify()
    except Exception as e:
        raise ValueError("Arquivo recebido não é uma imagem válida: {}".format(e))

    # get_or_create direto (e não TelegramUser.subscribe) para não reativar
    # a inscrição em alertas de quem já tinha enviado /stop
    telegram_user, _ = TelegramUser.objects.get_or_create(
        chat_id=chat_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'is_active': True,
        }
    )

    photo = TelegramPhoto(
        telegram_user=telegram_user,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_size=file_size,
        caption=caption or "",
        telegram_message_id=telegram_message_id,
        media_group_id=media_group_id or "",
        source=source,
    )

    photo.image.save(filename, ContentFile(image_bytes), save=True)

    return photo


class PhotoPermission:
    """Resultados possíveis de uma tentativa de enviar imagem ao bot"""

    ALLOWED = 'allowed'
    NOT_LINKED = 'not_linked'            # o chat não está ligado a nenhuma conta
    NOT_CONTRIBUTOR = 'not_contributor'  # conta vinculada, mas usuário comum


# Como em LinkResult: os campos saem daqui prontos, em string. O handler roda em
# contexto async e tocar em telegram_user.profile lá fora dispara uma consulta e
# levanta SynchronousOnlyOperation.
PhotoPermissionResult = namedtuple('PhotoPermissionResult', 'status profile_name')

# É esta permissão que separa contribuidor de usuário comum no envio de imagens.
# Concedida em accounts/permissions.py a `contributors` e `admins`; superusuário
# passa por bypass do has_perm.
UPLOAD_PERMISSION = 'telegram_bot.add_telegramphoto'


def photo_permission(chat_id):
    """Decide se este chat pode enviar imagens ao bot.

    A verificação é por permissão, e não por nome de grupo, para acompanhar o
    mesmo mapa que governa as telas do painel — ver accounts/permissions.py.

    Um usuário inativo também é barrado: o ModelBackend recusa has_perm() para
    quem tem is_active=False.
    """

    telegram_user = (
        TelegramUser.objects
        .select_related('profile__user')
        .filter(chat_id=chat_id)
        .first()
    )

    if telegram_user is None or telegram_user.profile is None:
        return PhotoPermissionResult(PhotoPermission.NOT_LINKED, '')

    profile = telegram_user.profile
    nome = profile.name or profile.user.username

    if not profile.user.has_perm(UPLOAD_PERMISSION):
        return PhotoPermissionResult(PhotoPermission.NOT_CONTRIBUTOR, nome)

    return PhotoPermissionResult(PhotoPermission.ALLOWED, nome)


def site_url(viewname):
    """URL absoluta de uma página do site, para citar nas mensagens do bot.

    Passa por reverse() e não por caminho fixo: se o prefixo das rotas do painel
    mudar, os textos do bot continuam corretos.
    """

    return "{}{}".format(settings.SITE_URL.rstrip('/'), reverse(viewname))


class LinkStatus:
    """Resultados possíveis de uma tentativa de vincular chat a conta"""

    OK = 'ok'
    ALREADY_LINKED = 'already_linked'   # este chat já estava vinculado a essa mesma conta
    NO_USERNAME = 'no_username'         # a conta do Telegram não tem @ definido
    NOT_FOUND = 'not_found'             # nenhum perfil do Labfito declarou esse @
    TAKEN = 'taken'                     # o perfil já está vinculado a OUTRO chat


# username/profile_name/telegram_username saem daqui como strings prontas para os
# handlers. Eles rodam em contexto async: tocar em telegram_user.profile ou
# profile.user lá fora dispara uma consulta e levanta SynchronousOnlyOperation.
LinkResult = namedtuple(
    'LinkResult',
    'status telegram_user profile username profile_name telegram_username'
)


def _resultado(status, telegram_user, profile=None):
    """Monta o LinkResult resolvendo as travessias de FK aqui, no lado síncrono"""

    return LinkResult(
        status=status,
        telegram_user=telegram_user,
        profile=profile,
        username=profile.user.username if profile else '',
        profile_name=(profile.name or profile.user.username) if profile else '',
        telegram_username=telegram_user.username if telegram_user else '',
    )


def link_by_telegram_username(chat_id, username, first_name=""):
    """Vincula o chat ao Profile que declarou este @username no Labfito.

    O @ vem da API do Telegram, não do texto que o usuário digita, e o perfil só
    é encontrado se o próprio dono da conta tiver informado esse @ no site —
    é isso que impede alguém de se cadastrar no bot com os dados de outra pessoa.

    Retorna um LinkResult; profile é None quando não houve vínculo.
    """

    username = normalize_telegram_username(username)

    telegram_user, _ = TelegramUser.objects.get_or_create(
        chat_id=chat_id,
        defaults={'username': username or '', 'first_name': first_name, 'is_active': True},
    )

    telegram_user.username = username or telegram_user.username
    telegram_user.first_name = first_name or telegram_user.first_name
    # /start é sempre um pedido explícito para voltar a receber, inclusive de
    # quem tinha enviado /stop antes — é o que a mensagem de /stop promete.
    telegram_user.is_active = True

    campos = ['username', 'first_name', 'is_active']

    if username is None:
        telegram_user.save(update_fields=campos)
        return _resultado(LinkStatus.NO_USERNAME, telegram_user)

    # select_related: o handler precisa do username da conta, e a travessia da FK
    # tem de acontecer aqui dentro.
    profile = Profile.objects.select_related('user').filter(telegram_username=username).first()

    if profile is None:
        telegram_user.save(update_fields=campos)
        if telegram_user.is_linked:
            # O @ mudou no Telegram depois do vínculo. Derrubar aqui deixaria a
            # pessoa sem alertas por um detalhe que ela já resolveu no site.
            vinculado = Profile.objects.select_related('user').get(pk=telegram_user.profile_id)
            return _resultado(LinkStatus.ALREADY_LINKED, telegram_user, vinculado)
        return _resultado(LinkStatus.NOT_FOUND, telegram_user)

    if telegram_user.profile_id == profile.pk:
        telegram_user.save(update_fields=campos)
        return _resultado(LinkStatus.ALREADY_LINKED, telegram_user, profile)

    if TelegramUser.objects.filter(profile=profile).exclude(pk=telegram_user.pk).exists():
        telegram_user.save(update_fields=campos)
        return _resultado(LinkStatus.TAKEN, telegram_user, profile)

    telegram_user.profile = profile
    telegram_user.linked_at = timezone.now()

    try:
        with transaction.atomic():
            telegram_user.save()
    except IntegrityError:
        # Dois chats tentando a mesma conta ao mesmo tempo — o OneToOne decide.
        telegram_user.refresh_from_db()
        return _resultado(LinkStatus.TAKEN, telegram_user, profile)

    return _resultado(LinkStatus.OK, telegram_user, profile)


def get_link_state(chat_id):
    """Retorna 'linked' ou 'unlinked' para um chat"""

    telegram_user = TelegramUser.objects.filter(chat_id=chat_id).first()

    if telegram_user is None or not telegram_user.is_linked:
        return 'unlinked'
    return 'linked'


def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    """Envia uma mensagem pela API HTTP do Telegram.

    Retorna (ok, status_code) — status_code é None quando a requisição nem saiu.
    """

    url = "{}{}/sendMessage".format(settings.TELEGRAM_API_URL, settings.TELEGRAM_BOT_TOKEN)
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}

    try:
        response = requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("❌ Erro ao enviar mensagem para {}: {}".format(chat_id, e))
        return False, None

    if response.status_code == 200:
        return True, 200

    print("❌ Erro API Telegram para {}: {} - {}".format(
        chat_id, response.status_code, response.text))
    return False, response.status_code


def broadcast_alert(message, users=None, parse_mode="Markdown"):
    """Envia `message` a todos que devem receber alertas.

    Retorna (enviados, total). Sem `users`, usa TelegramUser.objects.receiving_alerts().
    """

    if users is None:
        users = TelegramUser.objects.receiving_alerts()

    users = list(users)
    enviados = 0

    for usuario in users:
        ok, status = send_telegram_message(usuario.chat_id, message, parse_mode)

        if ok:
            enviados += 1
            usuario.last_alert_sent = timezone.now()
            usuario.save(update_fields=['last_alert_sent'])
        elif status == 403:
            # 403 = o usuário bloqueou o bot. Insistir só gera erro a cada alerta.
            usuario.is_active = False
            usuario.save(update_fields=['is_active'])

    return enviados, len(users)
