import os
import shutil
import tempfile
from io import BytesIO
from unittest.mock import Mock, patch

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from PIL import Image

from accounts.models import Profile
from telegram_bot.models import TelegramUser, TelegramPhoto
from telegram_bot.signals import sync_profile_link
from telegram_bot.services import (
    LinkStatus, PhotoPermission, broadcast_alert, get_link_state,
    link_by_telegram_username, photo_permission, save_incoming_photo, site_url,
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def make_image_bytes(size=(100, 80), fmt='PNG'):
    """Gera os bytes de uma imagem válida em memória"""
    buffer = BytesIO()
    Image.new('RGB', size, color='green').save(buffer, fmt)
    return buffer.getvalue()


def criar_profile(username, email, nome=None, telegram_username=None):
    """Cria um usuário e devolve o Profile que o signal criou para ele"""
    user = User.objects.create_user(username, email, 'senha-de-teste')
    profile = Profile.objects.get(user=user)
    profile.name = nome or username
    profile.telegram_username = telegram_username
    profile.save()
    return profile


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SaveIncomingPhotoTests(TestCase):
    """Testa a persistência de imagens recebidas pelo bot, sem depender da API do Telegram"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_cria_usuario_e_salva_arquivo(self):
        photo = save_incoming_photo(
            chat_id=123456,
            image_bytes=make_image_bytes(),
            filename='teste.png',
            username='fulano',
            first_name='Fulano',
        )

        self.assertEqual(TelegramUser.objects.count(), 1)
        self.assertEqual(TelegramPhoto.objects.count(), 1)
        self.assertEqual(photo.telegram_user.chat_id, 123456)
        self.assertTrue(os.path.exists(photo.image.path))
        self.assertEqual((photo.width, photo.height), (100, 80))
        self.assertTrue(photo.image.name.startswith('telegram/123456/'))

    def test_guarda_metadados_do_telegram(self):
        photo = save_incoming_photo(
            chat_id=999,
            image_bytes=make_image_bytes(),
            filename='doc.png',
            file_id='ABC123',
            file_unique_id='UNIQ123',
            file_size=4321,
            caption='folha com mancha',
            telegram_message_id=77,
            media_group_id='grupo-1',
            source='document',
        )

        photo.refresh_from_db()
        self.assertEqual(photo.file_id, 'ABC123')
        self.assertEqual(photo.file_unique_id, 'UNIQ123')
        self.assertEqual(photo.file_size, 4321)
        self.assertEqual(photo.caption, 'folha com mancha')
        self.assertEqual(photo.telegram_message_id, 77)
        self.assertEqual(photo.media_group_id, 'grupo-1')
        self.assertEqual(photo.source, 'document')

    def test_nao_reativa_usuario_que_cancelou_inscricao(self):
        TelegramUser.objects.create(chat_id=555, is_active=False)

        save_incoming_photo(chat_id=555, image_bytes=make_image_bytes(), filename='a.png')

        self.assertFalse(TelegramUser.objects.get(chat_id=555).is_active)

    def test_album_gera_um_registro_por_foto(self):
        for i in range(3):
            save_incoming_photo(
                chat_id=777,
                image_bytes=make_image_bytes(),
                filename='album-{}.png'.format(i),
                media_group_id='album-x',
            )

        self.assertEqual(TelegramPhoto.objects.filter(media_group_id='album-x').count(), 3)
        self.assertEqual(TelegramUser.objects.filter(chat_id=777).count(), 1)

    def test_arquivo_invalido_levanta_erro(self):
        with self.assertRaises(ValueError):
            save_incoming_photo(chat_id=1, image_bytes=b'nao sou imagem', filename='x.png')

        self.assertEqual(TelegramPhoto.objects.count(), 0)

    def test_bytes_vazios_levantam_erro(self):
        with self.assertRaises(ValueError):
            save_incoming_photo(chat_id=1, image_bytes=b'', filename='x.png')


class LinkByTelegramUsernameTests(TestCase):
    """Testa o vínculo do /start a partir do @ que a API do Telegram informa"""

    def test_vincula_quando_o_perfil_declarou_o_arroba(self):
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')

        resultado = link_by_telegram_username(100, 'ana_tg', first_name='Ana')

        self.assertEqual(resultado.status, LinkStatus.OK)
        self.assertEqual(resultado.profile, profile)
        self.assertEqual(resultado.telegram_user.profile, profile)
        self.assertIsNotNone(resultado.telegram_user.linked_at)
        self.assertTrue(resultado.telegram_user.is_active)

    def test_ignora_arroba_e_maiusculas(self):
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='@Ana_TG')

        resultado = link_by_telegram_username(101, '@ANA_tg')

        self.assertEqual(resultado.status, LinkStatus.OK)
        self.assertEqual(resultado.profile, profile)
        self.assertEqual(profile.telegram_username, 'ana_tg')

    def test_conta_do_telegram_sem_arroba(self):
        resultado = link_by_telegram_username(102, '')

        self.assertEqual(resultado.status, LinkStatus.NO_USERNAME)
        self.assertIsNone(resultado.profile)
        self.assertFalse(resultado.telegram_user.is_linked)

    def test_arroba_que_nenhum_perfil_declarou(self):
        criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')

        resultado = link_by_telegram_username(103, 'intruso')

        self.assertEqual(resultado.status, LinkStatus.NOT_FOUND)
        self.assertIsNone(resultado.profile)
        self.assertFalse(resultado.telegram_user.is_linked)

    def test_perfil_sem_arroba_nao_e_alcancado(self):
        """Perfil com o campo em branco não pode casar com um /start qualquer"""
        criar_profile('ana', 'ana@exemplo.com')

        resultado = link_by_telegram_username(104, '')

        self.assertEqual(resultado.status, LinkStatus.NO_USERNAME)
        self.assertEqual(TelegramUser.objects.linked().count(), 0)

    def test_perfil_ja_vinculado_a_outro_chat(self):
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        TelegramUser.objects.create(chat_id=105, username='ana_tg', profile=profile)

        resultado = link_by_telegram_username(106, 'ana_tg')

        self.assertEqual(resultado.status, LinkStatus.TAKEN)
        self.assertFalse(TelegramUser.objects.get(chat_id=106).is_linked)

    def test_start_repetido_e_idempotente(self):
        criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')

        link_by_telegram_username(107, 'ana_tg')
        resultado = link_by_telegram_username(107, 'ana_tg')

        self.assertEqual(resultado.status, LinkStatus.ALREADY_LINKED)

    def test_reativa_quem_tinha_dado_stop(self):
        criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        TelegramUser.objects.create(chat_id=108, username='ana_tg', is_active=False)

        resultado = link_by_telegram_username(108, 'ana_tg')

        self.assertTrue(resultado.telegram_user.is_active)
        self.assertTrue(TelegramUser.objects.get(chat_id=108).is_active)

    def test_trocar_de_arroba_no_telegram_nao_derruba_o_vinculo(self):
        """Quem já está vinculado não perde os alertas por mudar o @ no app"""
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        TelegramUser.objects.create(chat_id=109, username='ana_tg', profile=profile)

        resultado = link_by_telegram_username(109, 'ana_nova')

        self.assertEqual(resultado.status, LinkStatus.ALREADY_LINKED)
        self.assertEqual(resultado.profile, profile)
        self.assertEqual(resultado.username, 'ana')
        self.assertTrue(resultado.telegram_user.is_linked)

    def test_atualiza_dados_do_chat_existente(self):
        TelegramUser.objects.create(chat_id=110, username='antigo', first_name='Antigo')

        link_by_telegram_username(110, '@Novo_TG', first_name='Novo')

        telegram_user = TelegramUser.objects.get(chat_id=110)
        self.assertEqual(telegram_user.username, 'novo_tg')
        self.assertEqual(telegram_user.first_name, 'Novo')


class HandlerContractTests(TestCase):
    """Trava a costura async → ORM que já quebrou o /start uma vez.

    Os handlers são `async def`; qualquer travessia de FK feita fora do
    sync_to_async levanta SynchronousOnlyOperation. Por isso o serviço entrega
    username e profile_name já resolvidos, e é isso que este teste verifica.
    """

    def test_campos_de_texto_vem_prontos_do_servico(self):
        criar_profile('ana', 'ana@exemplo.com', nome='Ana Silva', telegram_username='ana_tg')

        async def fluxo():
            resultado = await sync_to_async(link_by_telegram_username)(400, 'ana_tg')
            # Exatamente o que _handle_start faz depois do await
            return resultado.status, resultado.username, resultado.profile_name, \
                resultado.telegram_username

        status, username, profile_name, telegram_username = async_to_sync(fluxo)()

        self.assertEqual(status, LinkStatus.OK)
        self.assertEqual(username, 'ana')
        self.assertEqual(profile_name, 'Ana Silva')
        self.assertEqual(telegram_username, 'ana_tg')

    def test_chat_ja_vinculado_tambem_traz_o_username(self):
        """O caminho ALREADY_LINKED precisa do username da conta para responder"""
        criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        link_by_telegram_username(401, 'ana_tg')

        async def fluxo():
            resultado = await sync_to_async(link_by_telegram_username)(401, 'ana_tg')
            return resultado.status, resultado.username

        self.assertEqual(async_to_sync(fluxo)(), (LinkStatus.ALREADY_LINKED, 'ana'))

    def test_arroba_trocado_no_telegram_tambem_traz_o_username(self):
        """Caminho que busca o perfil pelo profile_id — a FK também é travessia"""
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        TelegramUser.objects.create(chat_id=402, username='ana_tg', profile=profile)

        async def fluxo():
            resultado = await sync_to_async(link_by_telegram_username)(402, 'ana_nova')
            return resultado.status, resultado.username

        self.assertEqual(async_to_sync(fluxo)(), (LinkStatus.ALREADY_LINKED, 'ana'))


class SyncProfileLinkTests(TestCase):
    """Testa o reflexo do campo do perfil nos vínculos — o vínculo tardio"""

    def setUp(self):
        patcher = patch('telegram_bot.signals.send_telegram_message', return_value=(True, 200))
        self.enviar = patcher.start()
        self.addCleanup(patcher.stop)

    def test_vincula_chat_que_ja_tinha_dado_start(self):
        TelegramUser.objects.create(chat_id=200, username='ana_tg', first_name='Ana')
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')

        vinculado = sync_profile_link(profile)

        self.assertIsNotNone(vinculado)
        self.assertEqual(vinculado.chat_id, 200)
        self.assertEqual(TelegramUser.objects.get(chat_id=200).profile, profile)
        self.assertEqual(self.enviar.call_count, 1)
        self.assertEqual(self.enviar.call_args[0][0], 200)

    def test_nao_notifica_de_novo_em_saves_seguintes(self):
        TelegramUser.objects.create(chat_id=201, username='ana_tg')
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')

        sync_profile_link(profile)
        sync_profile_link(profile)

        self.assertEqual(self.enviar.call_count, 1)

    def test_trocar_o_arroba_desvincula_o_chat_antigo(self):
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        TelegramUser.objects.create(chat_id=202, username='ana_tg', profile=profile)

        profile.telegram_username = 'ana_nova'
        profile.save()
        sync_profile_link(profile)

        antigo = TelegramUser.objects.get(chat_id=202)
        self.assertFalse(antigo.is_linked)
        self.assertIsNone(antigo.linked_at)

    def test_apagar_o_arroba_desvincula(self):
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        TelegramUser.objects.create(chat_id=203, username='ana_tg', profile=profile)

        profile.telegram_username = ''
        profile.save()
        sync_profile_link(profile)

        self.assertFalse(TelegramUser.objects.get(chat_id=203).is_linked)
        self.assertEqual(TelegramUser.objects.receiving_alerts().count(), 0)

    def test_nao_rouba_chat_vinculado_a_outro_perfil(self):
        """O chat trocou de @ no Telegram; outro perfil declara o @ novo"""
        dona = criar_profile('bia', 'bia@exemplo.com', telegram_username='bia_tg')
        TelegramUser.objects.create(chat_id=204, username='chat_tg', profile=dona)

        outra = criar_profile('ana', 'ana@exemplo.com', telegram_username='chat_tg')

        self.assertIsNone(sync_profile_link(outra))
        self.assertEqual(TelegramUser.objects.get(chat_id=204).profile, dona)
        self.assertEqual(self.enviar.call_count, 0)

    def test_receiver_roda_ao_salvar_o_perfil(self):
        TelegramUser.objects.create(chat_id=205, username='ana_tg')
        profile = criar_profile('ana', 'ana@exemplo.com')

        with self.captureOnCommitCallbacks(execute=True):
            profile.telegram_username = '@Ana_TG'
            profile.save()

        self.assertEqual(TelegramUser.objects.get(chat_id=205).profile, profile)
        self.assertEqual(self.enviar.call_count, 1)


class GetLinkStateTests(TestCase):
    """Testa a leitura do estado da conversa"""

    def test_chat_desconhecido(self):
        self.assertEqual(get_link_state(300), 'unlinked')

    def test_chat_sem_conta_vinculada(self):
        link_by_telegram_username(301, 'ninguem_tg')
        self.assertEqual(get_link_state(301), 'unlinked')

    def test_apos_vincular_esta_linked(self):
        criar_profile('ana', 'ana@exemplo.com', telegram_username='ana_tg')
        link_by_telegram_username(302, 'ana_tg')

        self.assertEqual(get_link_state(302), 'linked')


class BackfillTelegramUsernameTests(TestCase):
    """Testa a migração de dados que herda o @ dos vínculos feitos por e-mail.

    A função da migração é chamada direto, com os models reais: o que importa é
    a regra de quem é preenchido e quem é pulado.
    """

    def backfill(self):
        from importlib import import_module

        from django.apps import apps as registro

        migracao = import_module('accounts.migrations.0006_backfill_telegram_username')
        migracao.backfill(registro, None)

    def test_preenche_a_partir_da_conversa_vinculada(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=600, username='Ana_TG', profile=profile)

        self.backfill()

        profile.refresh_from_db()
        self.assertEqual(profile.telegram_username, 'ana_tg')

    def test_nao_sobrescreve_quem_ja_declarou(self):
        profile = criar_profile('ana', 'ana@exemplo.com', telegram_username='escolhido')
        TelegramUser.objects.create(chat_id=601, username='outro_tg', profile=profile)

        self.backfill()

        profile.refresh_from_db()
        self.assertEqual(profile.telegram_username, 'escolhido')

    def test_ignora_conversa_sem_arroba(self):
        """O caso comum do fluxo por e-mail: o @ nunca chegou a ser gravado"""
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=602, username='', profile=profile)

        self.backfill()

        profile.refresh_from_db()
        self.assertIsNone(profile.telegram_username)

    def test_ignora_conversa_sem_vinculo(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=603, username='solto_tg')

        self.backfill()

        profile.refresh_from_db()
        self.assertIsNone(profile.telegram_username)

    def test_nao_duplica_arroba_ja_usado_por_outro_perfil(self):
        criar_profile('bia', 'bia@exemplo.com', telegram_username='ana_tg')
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=604, username='ana_tg', profile=profile)

        self.backfill()

        profile.refresh_from_db()
        self.assertIsNone(profile.telegram_username)

    def test_ignora_arroba_fora_do_formato_do_telegram(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=605, username='ab', profile=profile)

        self.backfill()

        profile.refresh_from_db()
        self.assertIsNone(profile.telegram_username)

    def test_e_idempotente(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=606, username='ana_tg', profile=profile)

        self.backfill()
        self.backfill()

        profile.refresh_from_db()
        self.assertEqual(profile.telegram_username, 'ana_tg')

    def test_o_vinculo_sobrevive_ao_proximo_save_do_perfil(self):
        """O ponto da migração: salvar o perfil não pode mais desfazer o vínculo"""
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=607, username='ana_tg', profile=profile)

        self.backfill()
        profile.refresh_from_db()
        sync_profile_link(profile, notify=False)

        self.assertEqual(TelegramUser.objects.get(chat_id=607).profile, profile)


class ReceivingAlertsQuerySetTests(TestCase):
    """Trava a regra central: só recebe alerta quem tem conta vinculada e ativa"""

    def test_exclui_chat_sem_conta_vinculada(self):
        TelegramUser.objects.create(chat_id=400, is_active=True)

        self.assertEqual(TelegramUser.objects.receiving_alerts().count(), 0)

    def test_exclui_chat_inativo_mesmo_vinculado(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        TelegramUser.objects.create(chat_id=401, is_active=False, profile=profile)

        self.assertEqual(TelegramUser.objects.receiving_alerts().count(), 0)

    def test_exclui_conta_do_django_desativada(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        profile.user.is_active = False
        profile.user.save()
        TelegramUser.objects.create(chat_id=402, profile=profile)

        self.assertEqual(TelegramUser.objects.receiving_alerts().count(), 0)

    def test_inclui_apenas_ativo_e_vinculado(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        esperado = TelegramUser.objects.create(chat_id=403, profile=profile)
        TelegramUser.objects.create(chat_id=404)

        recebendo = list(TelegramUser.objects.receiving_alerts())

        self.assertEqual(recebendo, [esperado])


class BroadcastAlertTests(TestCase):
    """Testa o envio compartilhado, sem tocar na API do Telegram"""

    def setUp(self):
        profile = criar_profile('ana', 'ana@exemplo.com')
        self.vinculado = TelegramUser.objects.create(chat_id=500, profile=profile)
        self.anonimo = TelegramUser.objects.create(chat_id=501)

    @patch('telegram_bot.services.requests.post')
    def test_envia_apenas_para_vinculados(self, post):
        post.return_value = Mock(status_code=200)

        enviados, total = broadcast_alert("alerta")

        self.assertEqual((enviados, total), (1, 1))
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args[1]['json']['chat_id'], 500)

    @patch('telegram_bot.services.requests.post')
    def test_registra_o_horario_do_ultimo_alerta(self, post):
        post.return_value = Mock(status_code=200)

        broadcast_alert("alerta")

        self.vinculado.refresh_from_db()
        self.assertIsNotNone(self.vinculado.last_alert_sent)

    @patch('telegram_bot.services.requests.post')
    def test_403_desativa_quem_bloqueou_o_bot(self, post):
        post.return_value = Mock(status_code=403, text='bot was blocked by the user')

        enviados, total = broadcast_alert("alerta")

        self.vinculado.refresh_from_db()
        self.assertEqual((enviados, total), (0, 1))
        self.assertFalse(self.vinculado.is_active)

    @patch('telegram_bot.services.requests.post')
    def test_sem_ninguem_vinculado_nao_envia(self, post):
        TelegramUser.objects.all().update(profile=None)

        enviados, total = broadcast_alert("alerta")

        self.assertEqual((enviados, total), (0, 0))
        post.assert_not_called()


# ---------------------------------------------------------------------------
# Envio de imagens: só contribuidor e administrador
# ---------------------------------------------------------------------------

def criar_profile_do_grupo(username, grupo, telegram_username=None, nome=None):
    """Profile cujo User já está em um dos grupos padrão"""

    profile = criar_profile(
        username, '{}@exemplo.com'.format(username),
        nome=nome, telegram_username=telegram_username,
    )
    profile.user.groups.add(Group.objects.get(name=grupo))

    return profile


def chat_vinculado(chat_id, profile):
    return TelegramUser.objects.create(chat_id=chat_id, profile=profile, is_active=True)


class PhotoPermissionTests(TestCase):
    """telegram_bot.services.photo_permission — a decisão de quem pode enviar"""

    def test_chat_desconhecido(self):
        resultado = photo_permission(999)

        self.assertEqual(resultado.status, PhotoPermission.NOT_LINKED)

    def test_chat_sem_conta_vinculada(self):
        TelegramUser.objects.create(chat_id=500, is_active=True)

        self.assertEqual(photo_permission(500).status, PhotoPermission.NOT_LINKED)

    def test_usuario_comum_e_recusado(self):
        profile = criar_profile_do_grupo('comum', 'common_users', nome='Ana Comum')
        chat_vinculado(501, profile)

        resultado = photo_permission(501)

        self.assertEqual(resultado.status, PhotoPermission.NOT_CONTRIBUTOR)
        # O nome vai na mensagem de recusa; precisa vir resolvido daqui
        self.assertEqual(resultado.profile_name, 'Ana Comum')

    def test_contribuidor_e_aceito(self):
        profile = criar_profile_do_grupo('contrib', 'contributors')
        chat_vinculado(502, profile)

        self.assertEqual(photo_permission(502).status, PhotoPermission.ALLOWED)

    def test_administrador_e_aceito(self):
        profile = criar_profile_do_grupo('adm', 'admins')
        chat_vinculado(503, profile)

        self.assertEqual(photo_permission(503).status, PhotoPermission.ALLOWED)

    def test_superusuario_passa_por_bypass(self):
        profile = criar_profile('root', 'root@exemplo.com')
        profile.user.is_superuser = True
        profile.user.save()
        chat_vinculado(504, profile)

        self.assertEqual(photo_permission(504).status, PhotoPermission.ALLOWED)

    def test_contribuidor_inativo_e_recusado(self):
        """has_perm() é False para is_active=False — conta desligada não envia"""

        profile = criar_profile_do_grupo('exilado', 'contributors')
        profile.user.is_active = False
        profile.user.save()
        chat_vinculado(505, profile)

        self.assertEqual(photo_permission(505).status, PhotoPermission.NOT_CONTRIBUTOR)

    def test_promover_a_contribuidor_libera_sem_mexer_no_vinculo(self):
        profile = criar_profile_do_grupo('subindo', 'common_users')
        chat_vinculado(506, profile)

        self.assertEqual(photo_permission(506).status, PhotoPermission.NOT_CONTRIBUTOR)

        profile.user.groups.clear()
        profile.user.groups.add(Group.objects.get(name='contributors'))

        self.assertEqual(photo_permission(506).status, PhotoPermission.ALLOWED)


class RespostaFake:
    """Substituto assíncrono de `message.reply_text` que guarda o que foi enviado.

    Um Mock comum devolveria None, e o handler faz `await` no retorno. O
    unittest.mock.AsyncMock só existe a partir do Python 3.8, e o container roda 3.7.
    """

    def __init__(self):
        self.textos = []

    async def __call__(self, text, **kwargs):
        self.textos.append(text)

    @property
    def call_count(self):
        return len(self.textos)


def update_de_foto(chat_id, media_group_id=None):
    """Um update do python-telegram-bot com uma foto, o bastante para o handler"""

    media = Mock(file_id='fid', file_unique_id='uid', file_size=1024)

    message = Mock(
        photo=[media],
        document=None,
        caption='',
        message_id=1,
        media_group_id=media_group_id,
    )
    message.reply_text = RespostaFake()

    update = Mock(message=message)
    update.effective_chat.id = chat_id
    update.effective_user.username = 'quem_enviou'
    update.effective_user.first_name = 'Quem'

    return update


async def _sem_download(*args, **kwargs):
    raise AssertionError("o handler não pode baixar o arquivo antes de checar a permissão")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class HandlePhotoPermissionTests(TestCase):
    """O handler recusa antes de baixar o arquivo e não grava nada"""

    def setUp(self):
        from telegram_bot.handlers import TelegramBot

        # __new__ sem __init__: instancia o singleton sem disparar o polling
        self.bot = TelegramBot.__new__(TelegramBot)
        self.bot._ultimo_album_recusado = {}

        # Qualquer tentativa de download falha o teste
        self.context = Mock()
        self.context.bot.get_file = _sem_download

    def responder(self, update):
        async_to_sync(self.bot._handle_photo)(update, self.context)

        return update.message.reply_text.textos[0]

    def test_chat_nao_vinculado_recebe_orientacao_e_nada_e_salvo(self):
        texto = self.responder(update_de_foto(600))

        self.assertIn('não está vinculada', texto)
        self.assertFalse(TelegramPhoto.objects.exists())

    def test_usuario_comum_e_orientado_a_solicitar_contribuidor(self):
        profile = criar_profile_do_grupo('comum', 'common_users', nome='Ana Comum')
        chat_vinculado(601, profile)

        texto = self.responder(update_de_foto(601))

        self.assertIn('não foi salva', texto)
        self.assertIn('contribuidor', texto)
        self.assertIn('Ana Comum', texto)
        self.assertFalse(TelegramPhoto.objects.exists())

    def test_a_recusa_cita_a_pagina_de_solicitacao(self):
        profile = criar_profile_do_grupo('comum', 'common_users')
        chat_vinculado(602, profile)

        texto = self.responder(update_de_foto(602))

        self.assertIn(site_url('dashboard:solicitation'), texto)

    def test_album_recusado_responde_uma_vez_so(self):
        profile = criar_profile_do_grupo('comum', 'common_users')
        chat_vinculado(603, profile)

        update1 = update_de_foto(603, media_group_id='alb1')
        update2 = update_de_foto(603, media_group_id='alb1')

        async_to_sync(self.bot._handle_photo)(update1, self.context)
        async_to_sync(self.bot._handle_photo)(update2, self.context)

        self.assertEqual(update1.message.reply_text.call_count, 1)
        self.assertEqual(update2.message.reply_text.call_count, 0)

    def test_fotos_avulsas_respondem_sempre(self):
        """Sem media_group_id não há álbum: cada foto merece sua resposta"""

        profile = criar_profile_do_grupo('comum', 'common_users')
        chat_vinculado(604, profile)

        update1 = update_de_foto(604)
        update2 = update_de_foto(604)

        async_to_sync(self.bot._handle_photo)(update1, self.context)
        async_to_sync(self.bot._handle_photo)(update2, self.context)

        self.assertEqual(update1.message.reply_text.call_count, 1)
        self.assertEqual(update2.message.reply_text.call_count, 1)

    def permitir_download(self):
        """Troca o get_file que falha por um que devolve uma imagem de verdade"""

        class ArquivoFake:
            async def download_as_bytearray(self):
                return bytearray(make_image_bytes())

        async def get_file(file_id):
            return ArquivoFake()

        self.context.bot.get_file = get_file

    def test_contribuidor_tem_a_imagem_salva(self):
        profile = criar_profile_do_grupo('contrib', 'contributors')
        chat_vinculado(605, profile)
        self.permitir_download()

        texto = self.responder(update_de_foto(605))

        self.assertIn('recebida com sucesso', texto)
        self.assertEqual(TelegramPhoto.objects.count(), 1)
        self.assertEqual(TelegramPhoto.objects.get().telegram_user.profile, profile)

    def test_administrador_tem_a_imagem_salva(self):
        profile = criar_profile_do_grupo('adm', 'admins')
        chat_vinculado(606, profile)
        self.permitir_download()

        self.responder(update_de_foto(606))

        self.assertEqual(TelegramPhoto.objects.count(), 1)

    def test_usuario_comum_nao_chega_a_baixar_o_arquivo(self):
        """A permissão é checada antes do get_file — 20 MB não são baixados à toa.

        O get_file deste teste continua sendo o que falha; se o handler o
        alcançasse, a resposta seria a mensagem de erro e não a de recusa.
        """

        profile = criar_profile_do_grupo('comum', 'common_users')
        chat_vinculado(607, profile)

        texto = self.responder(update_de_foto(607))

        self.assertIn('não foi salva', texto)
        self.assertNotIn('Tente novamente', texto)
