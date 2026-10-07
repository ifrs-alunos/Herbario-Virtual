"""Camada síncrona do bot do Telegram: imagens, vínculo de contas e envio.

Fica separada dos handlers do python-telegram-bot para poder ser testada e
reutilizada sem depender do loop de eventos nem da API do Telegram.
"""

import os
import posixpath
import re
from collections import namedtuple
from datetime import timedelta
from io import BytesIO

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image

from accounts.models import Profile, normalize_telegram_username
from telegram_bot.models import TRAINING_APPROVED_DIR, TelegramUser, TelegramPhoto

# Limite de download do método getFile da Bot API
MAX_TELEGRAM_FILE_SIZE = 20 * 1024 * 1024


# Imagens que chegam com menos que isto de intervalo formam um lote: a pergunta
# "treinar ou testar" é feita uma vez só. Um álbum chega como vários updates em
# sequência, e quem manda várias fotos avulsas costuma mandá-las de uma vez.
PENDING_BATCH_WINDOW = timedelta(minutes=2)

# Resposta do usuário -> uso da imagem (e pasta dentro de media-ia/)
PURPOSE_BY_ANSWER = {
    '1': TelegramPhoto.PURPOSE_TRAINING,
    '2': TelegramPhoto.PURPOSE_TEST,
}

# O handler roda em contexto async: sai daqui só o que ele precisa, pronto.
PendingPhoto = namedtuple('PendingPhoto', 'id file_id')


def register_pending_photo(chat_id, username="", first_name="", file_id="",
                           file_unique_id="", file_size=None, file_name="", caption="",
                           telegram_message_id=None, media_group_id="", source='photo'):
    """Registra uma imagem recebida, ainda sem baixar o arquivo.

    Retorna (photo, perguntar): perguntar é True quando a imagem abre um lote
    novo e o bot deve perguntar se ela é para treinar ou testar o modelo.
    """

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

    lote_aberto = TelegramPhoto.objects.pending().filter(
        telegram_user=telegram_user,
        received_at__gte=timezone.now() - PENDING_BATCH_WINDOW,
    ).exists()

    photo = TelegramPhoto.objects.create(
        telegram_user=telegram_user,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_size=file_size,
        file_name=file_name or "",
        caption=caption or "",
        telegram_message_id=telegram_message_id,
        media_group_id=media_group_id or "",
        source=source,
    )

    return photo, not lote_aberto


def pending_photos(chat_id):
    """Imagens deste chat aguardando a escolha entre treino e teste, da mais antiga à mais nova"""

    return [
        PendingPhoto(pk, file_id)
        for pk, file_id in TelegramPhoto.objects.pending()
        .filter(telegram_user__chat_id=chat_id)
        .order_by('received_at', 'pk')
        .values_list('pk', 'file_id')
    ]


def store_photo_file(photo_id, image_bytes, purpose):
    """Grava o arquivo em media-ia/ e marca o uso escolhido.

    Teste vai para test/. Treino vai para training/pending/, fica aguardando a
    descrição do usuário (ver save_descriptions) e depois a aprovação e a
    categorização de um administrador (ver approve_training_photo). Vale para
    todos, inclusive para quem é administrador.

    Levanta ValueError se os bytes não formarem uma imagem válida ou se o uso
    for desconhecido. O registro só é alterado se o arquivo for gravado.
    """

    if purpose not in dict(TelegramPhoto.PURPOSE_CHOICES):
        raise ValueError("Uso desconhecido: {}".format(purpose))

    if not image_bytes:
        raise ValueError("Nenhum dado de imagem recebido")

    # O ImageField só valida o conteúdo em formulários, então a verificação é feita aqui
    try:
        Image.open(BytesIO(image_bytes)).verify()
    except Exception as e:
        raise ValueError("Arquivo recebido não é uma imagem válida: {}".format(e))

    photo = TelegramPhoto.objects.pending().get(pk=photo_id)
    photo.purpose = purpose
    photo.classified_at = timezone.now()
    photo.awaiting_description = purpose == TelegramPhoto.PURPOSE_TRAINING
    if purpose == TelegramPhoto.PURPOSE_TRAINING:
        photo.review_status = TelegramPhoto.REVIEW_PENDING

    # O pk no nome liga o arquivo ao registro mesmo fora do banco
    nome = photo.file_name if photo.source == 'document' and photo.file_name \
        else "{}.jpg".format(photo.file_unique_id or 'imagem')
    photo.image.save("{}_{}".format(photo.pk, nome), ContentFile(image_bytes), save=True)

    return photo


def discard_pending_photo(photo_id):
    """Apaga o registro de uma imagem pendente que não pôde ser baixada ou validada"""

    TelegramPhoto.objects.pending().filter(pk=photo_id).delete()


# --- Descrição das imagens de treino ----------------------------------------

# O handler roda em contexto async: sai daqui só o que ele precisa, pronto.
DescriptionRequest = namedtuple('DescriptionRequest', 'number telegram_message_id')
DescriptionResult = namedtuple('DescriptionResult', 'saved missing')

# "1 - texto", "1 – texto", "1. texto", "1) texto", "1: texto"
NUMBERED_DESCRIPTION_RE = re.compile(r'^\s*(\d{1,3})\s*[-–—.):]\s*(.*)$')


def request_descriptions(chat_id):
    """Numera as imagens de treino deste chat que esperam descrição e as devolve.

    A numeração continua a das que já estavam esperando: quem manda um lote novo
    antes de descrever o anterior não vê dois "1". Retorna DescriptionRequest
    ordenados pelo número.
    """

    aguardando = TelegramPhoto.objects.awaiting_description().filter(telegram_user__chat_id=chat_id)

    with transaction.atomic():
        ultimo = max(
            [n for n in aguardando.values_list('description_number', flat=True) if n] or [0]
        )
        for photo in aguardando.filter(description_number__isnull=True).order_by('received_at', 'pk'):
            ultimo += 1
            photo.description_number = ultimo
            photo.save(update_fields=['description_number'])

    return [
        DescriptionRequest(numero, message_id)
        for numero, message_id in aguardando.order_by('description_number')
        .values_list('description_number', 'telegram_message_id')
    ]


def pending_description_numbers(chat_id):
    """Números das imagens deste chat que ainda esperam descrição, em ordem"""

    return list(
        TelegramPhoto.objects.awaiting_description()
        .filter(telegram_user__chat_id=chat_id)
        .order_by('description_number', 'pk')
        .values_list('description_number', flat=True)
    )


def parse_numbered_descriptions(text):
    """Separa "1 - texto" em {1: 'texto'}. Linhas sem número continuam a anterior.

    Um mesmo número repetido fica com o último texto.
    """

    descricoes = {}
    atual = None

    for linha in text.splitlines():
        casou = NUMBERED_DESCRIPTION_RE.match(linha)
        if casou:
            atual = int(casou.group(1))
            descricoes[atual] = casou.group(2).strip()
        elif atual is not None and linha.strip():
            descricoes[atual] = "{}\n{}".format(descricoes[atual], linha.strip()).strip()

    return {numero: texto for numero, texto in descricoes.items() if texto}


def save_descriptions(chat_id, text):
    """Grava as descrições que o usuário mandou para as imagens de treino.

    Com uma imagem só esperando, o texto inteiro é a descrição (aceitando também
    "1 - texto"). Com várias, só vale o formato numerado, e números que não
    correspondem a nenhuma imagem são ignorados. A imagem descrita sai da espera
    e passa a aparecer na tela de aprovação.

    Retorna DescriptionResult(saved, missing): os números gravados nesta mensagem
    e os que ainda faltam.
    """

    aguardando = {
        photo.description_number: photo
        for photo in TelegramPhoto.objects.awaiting_description().filter(telegram_user__chat_id=chat_id)
    }

    descricoes = parse_numbered_descriptions(text)

    if len(aguardando) == 1:
        numero = next(iter(aguardando))
        texto = descricoes.get(numero) or text.strip()
        # Um número sozinho ("1") é resposta a outra pergunta, não descrição
        descricoes = {numero: texto} if texto and not texto.isdigit() else {}

    salvas = []
    with transaction.atomic():
        for numero, texto in sorted(descricoes.items()):
            photo = aguardando.get(numero)
            if photo is None:
                continue
            photo.description = texto
            photo.awaiting_description = False
            photo.save(update_fields=['description', 'awaiting_description'])
            salvas.append(numero)

    faltam = sorted(numero for numero in aguardando if numero not in salvas)

    return DescriptionResult(salvas, faltam)


# --- Aprovação e categorização --------------------------------------------------

def training_file_name(photo, disease, state):
    """Nome do arquivo aprovado: data + chat_id + planta + doença + estado.

    Ex.: 2026-10-06_1620300780_soja_ferrugem-asiatica_doente.jpg. A data é a do
    envio ao bot. Cada parte passa por slugify, então o `_` só aparece como
    separador. Se o nome já existir, o armazenamento acrescenta um sufixo.
    """

    extensao = posixpath.splitext(photo.image.name)[1].lower() or '.jpg'

    partes = [
        timezone.localtime(photo.received_at).strftime('%Y-%m-%d'),
        str(photo.telegram_user.chat_id),
        slugify(disease.culture_disease.name),
        slugify(disease.name_disease),
        slugify(state),
    ]

    return "{}{}".format("_".join(partes), extensao)


def approve_training_photo(photo_id, user, disease, state):
    """Aprova e categoriza uma imagem de treino.

    Grava a doença e o estado escolhidos (a planta é a cultura da doença; o
    estado, um dos itens de disease.states) e move o arquivo para
    media-ia/training/approved/, renomeado por training_file_name.

    Levanta ValueError se o estado não estiver na lista da doença, e
    TelegramPhoto.DoesNotExist se a imagem não estiver aguardando aprovação (já
    aprovada, reprovada por outro administrador ou de teste).
    """

    if state not in disease.states:
        raise ValueError("O estado \"{}\" não pertence à doença \"{}\"".format(state, disease))

    with transaction.atomic():
        # select_for_update: dois administradores aprovando a mesma imagem ao
        # mesmo tempo — o segundo espera e cai no DoesNotExist.
        photo = (
            TelegramPhoto.objects.awaiting_approval()
            .select_for_update()
            .select_related('telegram_user')
            .get(pk=photo_id)
        )

        storage = photo.image.storage
        origem = photo.image.name
        destino = storage.get_available_name(
            posixpath.join(TRAINING_APPROVED_DIR, training_file_name(photo, disease, state))
        )

        os.makedirs(os.path.dirname(storage.path(destino)), exist_ok=True)
        os.replace(storage.path(origem), storage.path(destino))

        photo.image.name = destino
        photo.review_status = TelegramPhoto.REVIEW_APPROVED
        photo.reviewed_at = timezone.now()
        photo.reviewed_by = user
        photo.disease = disease
        photo.disease_state = state

        try:
            photo.save(update_fields=[
                'image', 'review_status', 'reviewed_at', 'reviewed_by', 'disease', 'disease_state',
            ])
        except Exception:
            # O banco não aceitou: devolve o arquivo para onde o registro aponta
            os.replace(storage.path(destino), storage.path(origem))
            raise

    return photo


def reject_training_photo(photo_id, user):
    """Reprova uma imagem de treino: registra a decisão e apaga o arquivo.

    O registro continua no banco com review_status='rejected', quem reprovou e
    quando, e a descrição de quem enviou. Só o arquivo some, e o campo image fica
    vazio para não apontar para um arquivo que não existe mais.

    Levanta TelegramPhoto.DoesNotExist se a imagem não estiver aguardando aprovação.
    """

    with transaction.atomic():
        photo = TelegramPhoto.objects.awaiting_approval().select_for_update().get(pk=photo_id)
        storage, nome = photo.image.storage, photo.image.name

        photo.image.name = ''
        photo.review_status = TelegramPhoto.REVIEW_REJECTED
        photo.reviewed_at = timezone.now()
        photo.reviewed_by = user
        photo.save(update_fields=['image', 'review_status', 'reviewed_at', 'reviewed_by'])

        # Só depois do commit: se a gravação da decisão falhar, o arquivo fica
        transaction.on_commit(lambda: storage.delete(nome))

    return photo


# Quem tem esta permissão aprova e categoriza as imagens de treino no painel.
# As próprias imagens dessa pessoa também passam pela tela de aprovação.
APPROVE_PERMISSION = 'telegram_bot.approve_telegramphoto'


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


class BotRole:
    """Tipos de conta para os quais o bot tem uma ajuda própria"""

    UNLINKED = 'unlinked'        # o chat não está ligado a nenhuma conta
    COMMON = 'common'            # usuário comum
    CONTRIBUTOR = 'contributor'  # pode enviar imagens
    ADMIN = 'admin'              # contribuidor que também revisa pedidos


BotRoleResult = namedtuple('BotRoleResult', 'role name')

# Revisar quem pede para virar contribuidor é o que o grupo `admins` tem e
# `contributors` não — ver ADMIN_PERMISSIONS em accounts/permissions.py.
REVIEW_PERMISSION = 'accounts.change_solicitation'


def bot_role(chat_id):
    """Decide qual ajuda mostrar a este chat, pelas permissões e não pelo nome do grupo.

    Pelo mesmo critério de photo_permission(): o contribuidor aqui é exatamente
    quem teria a imagem aceita. Superusuário cai em ADMIN pelo bypass do has_perm;
    conta desativada cai em COMMON, porque has_perm() recusa tudo a quem tem
    is_active=False. O nome sai pronto, em string, para o contexto async.
    """

    telegram_user = (
        TelegramUser.objects
        .select_related('profile__user')
        .filter(chat_id=chat_id)
        .first()
    )

    if telegram_user is None or telegram_user.profile is None:
        return BotRoleResult(BotRole.UNLINKED, '')

    user = telegram_user.profile.user
    nome = telegram_user.profile.name or user.username

    if user.has_perm(REVIEW_PERMISSION) and user.has_perm(UPLOAD_PERMISSION):
        return BotRoleResult(BotRole.ADMIN, nome)
    if user.has_perm(UPLOAD_PERMISSION):
        return BotRoleResult(BotRole.CONTRIBUTOR, nome)
    return BotRoleResult(BotRole.COMMON, nome)


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
