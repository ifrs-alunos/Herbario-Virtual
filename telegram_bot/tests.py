import os
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock, patch

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Profile
from disease.models import Culture, Disease
from telegram_bot.models import TelegramUser, TelegramPhoto
from telegram_bot.signals import sync_profile_link
from telegram_bot.services import (
    PENDING_BATCH_WINDOW, BotRole, LinkStatus, PhotoPermission, bot_role, broadcast_alert,
    discard_pending_photo, get_link_state, link_by_telegram_username, pending_photos,
    approve_training_photo, parse_numbered_descriptions, pending_description_numbers,
    photo_permission, register_pending_photo, reject_training_photo, request_descriptions,
    save_descriptions, site_url, store_photo_file,
)

TEMP_AI_MEDIA_ROOT = tempfile.mkdtemp()


def make_image_bytes(size=(100, 80), fmt='PNG'):
    """Gera os bytes de uma imagem válida em memória"""
    buffer = BytesIO()
    Image.new('RGB', size, color='green').save(buffer, fmt)
    return buffer.getvalue()


def criar_catalogo():
    """Soja → Ferrugem asiática → doente/saudável, e uma segunda doença sem estados"""

    soja = Culture.objects.create(name='Soja')
    ferrugem = Disease.objects.create(
        name_disease='Ferrugem asiática', scientific_name_disease='Phakopsora pachyrhizi',
        culture_disease=soja, symptoms_disease='Pústulas nas folhas', states=['doente', 'saudável'],
    )
    oidio = Disease.objects.create(
        name_disease='Oídio', scientific_name_disease='Erysiphe diffusa',
        culture_disease=soja, symptoms_disease='Pó branco nas folhas',
    )
    return soja, ferrugem, oidio, 'doente', 'saudável'


def descrever(photo, texto='Folha de soja'):
    """Marca a imagem de treino como já descrita pelo usuário, liberando a aprovação"""

    TelegramPhoto.objects.filter(pk=photo.pk).update(description=texto, awaiting_description=False)
    photo.refresh_from_db()
    return photo


def criar_profile(username, email, nome=None, telegram_username=None):
    """Cria um usuário e devolve o Profile que o signal criou para ele"""
    user = User.objects.create_user(username, email, 'senha-de-teste')
    profile = Profile.objects.get(user=user)
    profile.name = nome or username
    profile.telegram_username = telegram_username
    profile.save()
    return profile


class RegisterPendingPhotoTests(TestCase):
    """O registro nasce sem arquivo, e só a primeira imagem de um lote pede a pergunta"""

    def test_cria_usuario_e_registro_sem_arquivo(self):
        photo, perguntar = register_pending_photo(
            chat_id=123456, username='fulano', first_name='Fulano', file_id='F1',
        )

        self.assertTrue(perguntar)
        self.assertEqual(TelegramUser.objects.count(), 1)
        self.assertEqual(photo.telegram_user.chat_id, 123456)
        self.assertEqual(photo.purpose, '')
        self.assertFalse(photo.image)

    def test_guarda_metadados_do_telegram(self):
        photo, _ = register_pending_photo(
            chat_id=999,
            file_id='ABC123',
            file_unique_id='UNIQ123',
            file_size=4321,
            file_name='folha.png',
            caption='folha com mancha',
            telegram_message_id=77,
            media_group_id='grupo-1',
            source='document',
        )

        photo.refresh_from_db()
        self.assertEqual(photo.file_id, 'ABC123')
        self.assertEqual(photo.file_unique_id, 'UNIQ123')
        self.assertEqual(photo.file_size, 4321)
        self.assertEqual(photo.file_name, 'folha.png')
        self.assertEqual(photo.caption, 'folha com mancha')
        self.assertEqual(photo.telegram_message_id, 77)
        self.assertEqual(photo.media_group_id, 'grupo-1')
        self.assertEqual(photo.source, 'document')

    def test_nao_reativa_usuario_que_cancelou_inscricao(self):
        TelegramUser.objects.create(chat_id=555, is_active=False)

        register_pending_photo(chat_id=555)

        self.assertFalse(TelegramUser.objects.get(chat_id=555).is_active)

    def test_album_pergunta_uma_vez_so(self):
        respostas = [
            register_pending_photo(chat_id=777, media_group_id='album-x')[1]
            for _ in range(3)
        ]

        self.assertEqual(respostas, [True, False, False])
        self.assertEqual(len(pending_photos(777)), 3)

    def test_lote_antigo_sem_resposta_volta_a_perguntar(self):
        antiga, _ = register_pending_photo(chat_id=778)
        TelegramPhoto.objects.filter(pk=antiga.pk).update(
            received_at=timezone.now() - PENDING_BATCH_WINDOW - timedelta(seconds=1)
        )

        _, perguntar = register_pending_photo(chat_id=778)

        self.assertTrue(perguntar)
        # A resposta à nova pergunta vale também para a imagem antiga
        self.assertEqual(len(pending_photos(778)), 2)

    def test_lote_de_outro_chat_nao_interfere(self):
        register_pending_photo(chat_id=779)

        _, perguntar = register_pending_photo(chat_id=780)

        self.assertTrue(perguntar)

    def test_registro_anterior_ao_fluxo_nao_e_pendente(self):
        """Imagens gravadas antes desta mudança têm arquivo, mas nenhum uso"""

        telegram_user = TelegramUser.objects.create(chat_id=781)
        TelegramPhoto.objects.create(
            telegram_user=telegram_user, image='telegram/781/antiga.jpg', width=10, height=10,
        )

        self.assertEqual(pending_photos(781), [])


@override_settings(AI_MEDIA_ROOT=TEMP_AI_MEDIA_ROOT)
class StorePhotoFileTests(TestCase):
    """O binário vai para media-ia/<uso>/ e o banco guarda só o caminho"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_AI_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def pendente(self, **kwargs):
        kwargs.setdefault('file_unique_id', 'UNIQ')
        return register_pending_photo(chat_id=123, **kwargs)[0]

    def test_treino_vai_para_a_pasta_training_pending(self):
        photo = store_photo_file(self.pendente().pk, make_image_bytes(), 'training')

        self.assertEqual(photo.purpose, 'training')
        self.assertIsNotNone(photo.classified_at)
        self.assertIsNone(photo.reviewed_at)
        self.assertTrue(photo.image.name.startswith('training/pending/'))
        # Só entra na fila de aprovação depois que o usuário descreve a imagem
        self.assertEqual(list(TelegramPhoto.objects.awaiting_description()), [photo])
        self.assertFalse(TelegramPhoto.objects.awaiting_approval().exists())
        self.assertEqual(
            photo.image.path,
            os.path.join(os.path.abspath(TEMP_AI_MEDIA_ROOT), photo.image.name),
        )
        self.assertTrue(os.path.exists(photo.image.path))
        self.assertEqual((photo.width, photo.height), (100, 80))

    def test_teste_vai_para_a_pasta_test(self):
        photo = store_photo_file(self.pendente().pk, make_image_bytes(), 'test')

        self.assertTrue(photo.image.name.startswith('test/'))
        self.assertTrue(os.path.exists(photo.image.path))
        # Teste não depende de aprovação
        self.assertFalse(TelegramPhoto.objects.awaiting_approval().exists())

    def test_nome_do_arquivo_comeca_pelo_id_do_registro(self):
        foto = store_photo_file(self.pendente().pk, make_image_bytes(), 'test')
        documento = store_photo_file(
            self.pendente(source='document', file_name='folha.png').pk,
            make_image_bytes(), 'test',
        )

        self.assertEqual(foto.image.name, 'test/{}_UNIQ.jpg'.format(foto.pk))
        self.assertEqual(documento.image.name, 'test/{}_folha.png'.format(documento.pk))

    def test_imagem_deixa_de_ser_pendente(self):
        photo = self.pendente()

        store_photo_file(photo.pk, make_image_bytes(), 'training')

        self.assertEqual(pending_photos(123), [])

    def test_arquivo_invalido_nao_altera_o_registro(self):
        photo = self.pendente()

        with self.assertRaises(ValueError):
            store_photo_file(photo.pk, b'nao sou imagem', 'training')

        photo.refresh_from_db()
        self.assertEqual(photo.purpose, '')
        self.assertFalse(photo.image)

    def test_bytes_vazios_levantam_erro(self):
        with self.assertRaises(ValueError):
            store_photo_file(self.pendente().pk, b'', 'training')

    def test_uso_desconhecido_levanta_erro(self):
        with self.assertRaises(ValueError):
            store_photo_file(self.pendente().pk, make_image_bytes(), 'outro')

    def test_imagem_ja_classificada_nao_e_regravada(self):
        photo = store_photo_file(self.pendente().pk, make_image_bytes(), 'training')

        with self.assertRaises(TelegramPhoto.DoesNotExist):
            store_photo_file(photo.pk, make_image_bytes(), 'test')

    def test_descartar_apaga_so_pendentes(self):
        pendente = self.pendente()
        gravada = store_photo_file(self.pendente().pk, make_image_bytes(), 'test')

        discard_pending_photo(pendente.pk)
        discard_pending_photo(gravada.pk)

        self.assertEqual(list(TelegramPhoto.objects.values_list('pk', flat=True)), [gravada.pk])


@override_settings(AI_MEDIA_ROOT=TEMP_AI_MEDIA_ROOT)
class RevisaoImagemTreinoTests(TestCase):
    """Aprovar categoriza e move para training/approved/ com nome data_chat_planta_doenca_estado; reprovar guarda a decisão e apaga só o arquivo"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_AI_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.revisor = User.objects.create_user('revisor', 'revisor@exemplo.com', 'senha-de-teste')
        self.soja, self.ferrugem, self.oidio, self.doente, self.saudavel = criar_catalogo()

    def gravada(self, purpose='training', unique='TREINO', chat_id=321):
        pendente, _ = register_pending_photo(chat_id=chat_id, file_unique_id=unique)
        photo = store_photo_file(pendente.pk, make_image_bytes(), purpose)
        return descrever(photo) if purpose == 'training' else photo

    def aprovar(self, photo, state=None):
        return approve_training_photo(photo.pk, self.revisor, self.ferrugem, state or self.doente)

    def nome_esperado(self, photo, estado='doente', ext='.jpg'):
        data = timezone.localtime(photo.received_at).strftime('%Y-%m-%d')
        return 'training/approved/{}_{}_soja_ferrugem-asiatica_{}{}'.format(
            data, photo.telegram_user.chat_id, estado, ext)

    def test_aprovar_categoriza_e_move_para_approved(self):
        photo = self.gravada()
        origem = photo.image.path

        aprovada = self.aprovar(photo)

        aprovada.refresh_from_db()
        self.assertEqual(aprovada.image.name, self.nome_esperado(photo))
        self.assertTrue(os.path.exists(aprovada.image.path))
        self.assertFalse(os.path.exists(origem))
        self.assertEqual(aprovada.review_status, 'approved')
        self.assertEqual(aprovada.reviewed_by, self.revisor)
        self.assertIsNotNone(aprovada.reviewed_at)
        self.assertEqual(aprovada.disease, self.ferrugem)
        self.assertEqual(aprovada.disease_state, self.doente)
        self.assertFalse(TelegramPhoto.objects.awaiting_approval().exists())
        self.assertEqual(list(TelegramPhoto.objects.approved()), [aprovada])

    def test_acento_do_estado_vira_ascii_no_nome(self):
        photo = self.gravada()

        aprovada = self.aprovar(photo, self.saudavel)

        self.assertEqual(aprovada.image.name, self.nome_esperado(photo, 'saudavel'))

    def test_mesmo_nome_nao_sobrescreve(self):
        primeira = self.aprovar(self.gravada(unique='A'))
        segunda = self.aprovar(self.gravada(unique='B'))

        self.assertNotEqual(primeira.image.name, segunda.image.name)
        self.assertTrue(os.path.exists(primeira.image.path))
        self.assertTrue(os.path.exists(segunda.image.path))

    def test_aprovar_imagem_antiga_gravada_direto_em_training(self):
        photo = self.gravada()
        antigo = 'training/{}_antiga.png'.format(photo.pk)
        os.replace(photo.image.path, photo.image.storage.path(antigo))
        TelegramPhoto.objects.filter(pk=photo.pk).update(image=antigo)

        aprovada = self.aprovar(photo)

        self.assertEqual(aprovada.image.name, self.nome_esperado(photo, ext='.png'))
        self.assertTrue(os.path.exists(aprovada.image.path))

    def test_estado_de_outra_doenca_e_recusado(self):
        photo = self.gravada()

        with self.assertRaises(ValueError):
            approve_training_photo(photo.pk, self.revisor, self.oidio, self.doente)

        photo.refresh_from_db()
        self.assertIsNone(photo.reviewed_at)
        self.assertTrue(os.path.exists(photo.image.path))

    def test_treino_espera_a_descricao_antes_da_aprovacao(self):
        pendente, _ = register_pending_photo(chat_id=325, file_unique_id='DESC')

        photo = store_photo_file(pendente.pk, make_image_bytes(), 'training')

        self.assertTrue(photo.awaiting_description)
        self.assertFalse(TelegramPhoto.objects.awaiting_approval().exists())
        with self.assertRaises(TelegramPhoto.DoesNotExist):
            self.aprovar(photo)

    def test_treino_de_administrador_tambem_espera_aprovacao(self):
        chat_vinculado(322, criar_profile_do_grupo('adm', 'admins'))
        pendente, _ = register_pending_photo(chat_id=322, file_unique_id='ADM')

        photo = store_photo_file(pendente.pk, make_image_bytes(), 'training')

        self.assertEqual(photo.image.name, 'training/pending/{}_ADM.jpg'.format(photo.pk))
        self.assertIsNone(photo.reviewed_at)
        self.assertIsNone(photo.reviewed_by)
        self.assertTrue(photo.awaiting_description)

    def test_treino_de_contribuidor_espera_aprovacao(self):
        chat_vinculado(323, criar_profile_do_grupo('contrib', 'contributors'))
        pendente, _ = register_pending_photo(chat_id=323, file_unique_id='CTB')

        photo = store_photo_file(pendente.pk, make_image_bytes(), 'training')

        self.assertTrue(photo.image.name.startswith('training/pending/'))
        self.assertIsNone(photo.reviewed_at)

    def test_teste_de_administrador_continua_em_test(self):
        chat_vinculado(324, criar_profile_do_grupo('adm', 'admins'))
        pendente, _ = register_pending_photo(chat_id=324, file_unique_id='T')

        photo = store_photo_file(pendente.pk, make_image_bytes(), 'test')

        self.assertTrue(photo.image.name.startswith('test/'))
        self.assertIsNone(photo.reviewed_at)
        self.assertFalse(photo.awaiting_description)

    def test_nao_aprova_duas_vezes_nem_imagem_de_teste(self):
        photo = self.gravada()
        self.aprovar(photo)
        teste = self.gravada(purpose='test', unique='TESTE')

        with self.assertRaises(TelegramPhoto.DoesNotExist):
            self.aprovar(photo)
        with self.assertRaises(TelegramPhoto.DoesNotExist):
            self.aprovar(teste)

    def test_reprovar_guarda_a_decisao_e_apaga_so_o_arquivo(self):
        photo = self.gravada()
        caminho = photo.image.path

        with self.captureOnCommitCallbacks(execute=True):
            reject_training_photo(photo.pk, self.revisor)

        photo.refresh_from_db()
        self.assertEqual(photo.review_status, 'rejected')
        self.assertEqual(photo.reviewed_by, self.revisor)
        self.assertIsNotNone(photo.reviewed_at)
        self.assertEqual(photo.description, 'Folha de soja')
        self.assertFalse(photo.image)
        self.assertFalse(os.path.exists(caminho))
        self.assertEqual(list(TelegramPhoto.objects.rejected()), [photo])
        self.assertFalse(TelegramPhoto.objects.awaiting_approval().exists())
        self.assertFalse(TelegramPhoto.objects.approved().exists())

    def test_arquivo_so_e_apagado_depois_do_commit(self):
        photo = self.gravada()

        with self.captureOnCommitCallbacks(execute=False):
            reject_training_photo(photo.pk, self.revisor)

        self.assertTrue(os.path.exists(photo.image.path))

    def test_imagem_nova_comeca_aguardando_revisao(self):
        self.assertEqual(self.gravada().review_status, 'pending')
        self.assertEqual(self.gravada(purpose='test', unique='T').review_status, '')

    def test_nao_reprova_imagem_aprovada_nem_de_teste(self):
        aprovada = self.aprovar(self.gravada())
        teste = self.gravada(purpose='test', unique='TESTE')

        for photo in (aprovada, teste):
            with self.assertRaises(TelegramPhoto.DoesNotExist):
                reject_training_photo(photo.pk, self.revisor)
            self.assertTrue(os.path.exists(photo.image.path))

        aprovada.refresh_from_db()
        self.assertEqual(aprovada.review_status, 'approved')

    def test_nao_aprova_imagem_reprovada(self):
        photo = self.gravada()
        reject_training_photo(photo.pk, self.revisor)

        with self.assertRaises(TelegramPhoto.DoesNotExist):
            self.aprovar(photo)


class EstadosDaDoencaTests(TestCase):
    """Os estados ficam numa lista dentro da própria doença"""

    def test_cada_doenca_tem_a_sua_lista(self):
        _, ferrugem, oidio, _, _ = criar_catalogo()

        self.assertEqual(ferrugem.states, ['doente', 'saudável'])
        self.assertEqual(oidio.states, [])

    def test_save_limpa_espacos_e_itens_vazios(self):
        _, ferrugem, _, _, _ = criar_catalogo()
        ferrugem.states = [' doente ', '', '  ', 'saudável']
        ferrugem.save()

        ferrugem.refresh_from_db()
        self.assertEqual(ferrugem.states, ['doente', 'saudável'])

    def test_add_state_nao_duplica_ignorando_maiusculas(self):
        _, ferrugem, _, _, _ = criar_catalogo()

        self.assertEqual(ferrugem.add_state('Doente'), 'doente')
        self.assertEqual(ferrugem.add_state(' esporulando '), 'esporulando')

        ferrugem.refresh_from_db()
        self.assertEqual(ferrugem.states, ['doente', 'saudável', 'esporulando'])


@override_settings(AI_MEDIA_ROOT=TEMP_AI_MEDIA_ROOT)
class DescricaoImagemTreinoTests(TestCase):
    """Cada imagem de treino recebe um número e precisa de uma descrição antes da aprovação"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_AI_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def gravar(self, total, chat_id=800):
        fotos = []
        for i in range(total):
            pendente, _ = register_pending_photo(
                chat_id=chat_id, file_unique_id='D{}'.format(i), telegram_message_id=100 + i)
            fotos.append(store_photo_file(pendente.pk, make_image_bytes(), 'training'))
        return fotos

    def test_numera_na_ordem_de_chegada_e_devolve_a_mensagem_de_cada_uma(self):
        self.gravar(3)

        pedidos = request_descriptions(800)

        self.assertEqual([(p.number, p.telegram_message_id) for p in pedidos], [(1, 100), (2, 101), (3, 102)])

    def test_lote_novo_continua_a_numeracao(self):
        self.gravar(2)
        request_descriptions(800)
        pendente, _ = register_pending_photo(chat_id=800, file_unique_id='NOVA', telegram_message_id=200)
        store_photo_file(pendente.pk, make_image_bytes(), 'training')

        pedidos = request_descriptions(800)

        self.assertEqual([p.number for p in pedidos], [1, 2, 3])
        self.assertEqual(pedidos[-1].telegram_message_id, 200)

    def test_uma_imagem_aceita_o_texto_inteiro(self):
        self.gravar(1)
        request_descriptions(800)

        resultado = save_descriptions(800, '  Soja com ferrugem  ')

        self.assertEqual((resultado.saved, resultado.missing), ([1], []))
        photo = TelegramPhoto.objects.get()
        self.assertEqual(photo.description, 'Soja com ferrugem')
        self.assertFalse(photo.awaiting_description)
        self.assertEqual(list(TelegramPhoto.objects.awaiting_approval()), [photo])

    def test_uma_imagem_aceita_o_formato_numerado(self):
        self.gravar(1)
        request_descriptions(800)

        save_descriptions(800, '1 - Soja saudável')

        self.assertEqual(TelegramPhoto.objects.get().description, 'Soja saudável')

    def test_um_numero_sozinho_nao_e_descricao(self):
        self.gravar(1)
        request_descriptions(800)

        resultado = save_descriptions(800, '2')

        self.assertEqual((resultado.saved, resultado.missing), ([], [1]))

    def test_varias_imagens_numa_mensagem_so(self):
        self.gravar(3)
        request_descriptions(800)

        resultado = save_descriptions(800, '1 - Soja saudável\n2 – Ferrugem\ncom muitas pústulas\n3) Oídio')

        self.assertEqual((resultado.saved, resultado.missing), ([1, 2, 3], []))
        descricoes = dict(TelegramPhoto.objects.values_list('description_number', 'description'))
        self.assertEqual(descricoes, {1: 'Soja saudável', 2: 'Ferrugem\ncom muitas pústulas', 3: 'Oídio'})

    def test_varias_imagens_aos_poucos(self):
        self.gravar(3)
        request_descriptions(800)

        primeira = save_descriptions(800, '2 - Ferrugem')
        segunda = save_descriptions(800, '1 - Saudável\n3 - Oídio')

        self.assertEqual((primeira.saved, primeira.missing), ([2], [1, 3]))
        self.assertEqual((segunda.saved, segunda.missing), ([1, 3], []))
        self.assertEqual(pending_description_numbers(800), [])

    def test_varias_imagens_sem_numero_nao_grava_nada(self):
        self.gravar(2)
        request_descriptions(800)

        resultado = save_descriptions(800, 'Soja com ferrugem')

        self.assertEqual((resultado.saved, resultado.missing), ([], [1, 2]))

    def test_numero_inexistente_e_ignorado(self):
        self.gravar(2)
        request_descriptions(800)

        resultado = save_descriptions(800, '1 - Saudável\n7 - Não existe')

        self.assertEqual((resultado.saved, resultado.missing), ([1], [2]))

    def test_nao_mexe_nas_imagens_de_outro_chat(self):
        self.gravar(1, chat_id=800)
        self.gravar(1, chat_id=801)
        request_descriptions(800)
        request_descriptions(801)

        save_descriptions(800, 'Soja')

        self.assertEqual(pending_description_numbers(801), [1])

    def test_parse_ignora_linha_antes_do_primeiro_numero(self):
        self.assertEqual(parse_numbered_descriptions('Seguem:\n1. A\n2: B'), {1: 'A', 2: 'B'})


@override_settings(AI_MEDIA_ROOT=TEMP_AI_MEDIA_ROOT)
class PainelModelosIATests(TestCase):
    """Tela "Modelos de IA" do painel: só o grupo admins aprova e categoriza"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_AI_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.soja, self.ferrugem, self.oidio, self.doente, self.saudavel = criar_catalogo()
        pendente, _ = register_pending_photo(chat_id=654, file_unique_id='PAINEL')
        self.photo = descrever(
            store_photo_file(pendente.pk, make_image_bytes(), 'training'), 'Folha com pústulas')

    def entrar(self, grupo):
        profile = criar_profile_do_grupo(grupo, grupo)
        self.client.login(username=profile.user.username, password='senha-de-teste')
        return profile.user

    def aprovar(self, **dados):
        dados.setdefault('culture', self.soja.pk)
        dados.setdefault('disease', self.ferrugem.pk)
        if 'new_state' not in dados:
            dados.setdefault('state', self.doente)
        return self.client.post(
            reverse('dashboard:ai_model_photo_approve', args=[self.photo.pk]), dados, follow=True)

    def test_admin_ve_a_lista_a_descricao_e_as_opcoes(self):
        self.entrar('admins')

        pagina = self.client.get(reverse('dashboard:ai_model_review'))

        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, 'Modelos de IA')
        self.assertContains(pagina, 'Folha com pústulas')
        self.assertContains(pagina, '<option value="{}">Soja</option>'.format(self.soja.pk), html=True)
        # As doenças vão no JSON dos selects, que escapa os acentos
        self.assertEqual(
            {d['name'] for d in pagina.context['catalog']['diseases']}, {'Ferrugem asiática', 'Oídio'})
        self.assertContains(pagina, 'id="ai-model-catalog"')
        self.assertContains(pagina, reverse('dashboard:ai_model_photo_file', args=[self.photo.pk]))

        arquivo = self.client.get(reverse('dashboard:ai_model_photo_file', args=[self.photo.pk]))
        self.assertEqual(b''.join(arquivo.streaming_content), make_image_bytes())

    def test_imagem_sem_descricao_nao_aparece(self):
        self.entrar('admins')
        TelegramPhoto.objects.filter(pk=self.photo.pk).update(awaiting_description=True)

        pagina = self.client.get(reverse('dashboard:ai_model_review'))

        self.assertNotContains(pagina, reverse('dashboard:ai_model_photo_file', args=[self.photo.pk]))
        self.assertContains(pagina, 'Aguardando a descrição de quem enviou: 1')

    def test_contribuidor_nao_revisa(self):
        self.entrar('contributors')

        for nome in ('dashboard:ai_model_review', 'dashboard:ai_model_photo_file'):
            args = [] if nome == 'dashboard:ai_model_review' else [self.photo.pk]
            self.assertEqual(self.client.get(reverse(nome, args=args)).status_code, 403)
        resposta = self.aprovar()

        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(TelegramPhoto.objects.awaiting_approval().filter(pk=self.photo.pk).exists())
        self.assertNotContains(self.client.get(reverse('dashboard:profile')), 'Modelos de IA')

    def test_admin_aprova_por_post_com_categoria(self):
        admin = self.entrar('admins')

        self.assertEqual(
            self.client.get(reverse('dashboard:ai_model_photo_approve', args=[self.photo.pk])).status_code,
            405,
        )
        resposta = self.aprovar()

        self.assertRedirects(resposta, reverse('dashboard:ai_model_review'))
        self.assertContains(resposta, 'aprovada e salva no treino')
        self.photo.refresh_from_db()
        self.assertTrue(self.photo.image.name.startswith('training/approved/'))
        self.assertTrue(self.photo.image.name.endswith('_654_soja_ferrugem-asiatica_doente.jpg'))
        self.assertEqual(self.photo.review_status, 'approved')
        self.assertEqual(self.photo.reviewed_by, admin)
        self.assertEqual(self.photo.disease, self.ferrugem)
        self.assertEqual(self.photo.disease_state, self.doente)

    def test_novo_estado_e_criado_para_a_doenca(self):
        self.entrar('admins')

        self.aprovar(disease=self.oidio.pk, new_state=' esporulando ')

        self.oidio.refresh_from_db()
        self.assertEqual(self.oidio.states, ['esporulando'])
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.disease_state, 'esporulando')

    def test_novo_estado_com_nome_existente_reaproveita(self):
        self.entrar('admins')

        self.aprovar(new_state='Doente')

        self.ferrugem.refresh_from_db()
        self.assertEqual(self.ferrugem.states, ['doente', 'saudável'])
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.disease_state, self.doente)

    def test_combinacoes_invalidas_nao_aprovam(self):
        self.entrar('admins')
        outra = Culture.objects.create(name='Milho')

        casos = [
            {'culture': outra.pk},                         # doença não é da planta
            {'disease': self.oidio.pk},                    # estado não é da doença
            {'state': ''},                                 # sem estado
            {'new_state': 'novo', 'state': self.doente},  # os dois
        ]
        for dados in casos:
            resposta = self.aprovar(**dados)
            self.assertContains(resposta, 'não aprovada', msg_prefix=str(dados))

        self.assertTrue(TelegramPhoto.objects.awaiting_approval().filter(pk=self.photo.pk).exists())
        for disease in Disease.objects.all():
            self.assertNotIn('novo', disease.states)

    def test_admin_reprova_por_post(self):
        admin = self.entrar('admins')
        caminho = self.photo.image.path

        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(reverse('dashboard:ai_model_photo_reject', args=[self.photo.pk]))

        self.assertRedirects(resposta, reverse('dashboard:ai_model_review'))
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.review_status, 'rejected')
        self.assertEqual(self.photo.reviewed_by, admin)
        self.assertFalse(os.path.exists(caminho))

        pagina = self.client.get(reverse('dashboard:ai_model_review'))
        self.assertContains(pagina, 'Reprovadas: 1')
        self.assertNotContains(pagina, reverse('dashboard:ai_model_photo_file', args=[self.photo.pk]))

    def test_imagem_ja_revisada_so_avisa(self):
        self.entrar('admins')
        self.aprovar()

        resposta = self.client.post(
            reverse('dashboard:ai_model_photo_reject', args=[self.photo.pk]), follow=True,
        )
        self.assertContains(resposta, 'já foi revisada')

        resposta = self.aprovar(new_state='outro')
        self.assertContains(resposta, 'já foi revisada')
        # O estado digitado não sobra quando a aprovação não acontece
        self.ferrugem.refresh_from_db()
        self.assertNotIn('outro', self.ferrugem.states)
        self.assertTrue(TelegramPhoto.objects.filter(pk=self.photo.pk).exists())


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


class HandlePhotoPermissionTests(TestCase):
    """O handler recusa sem registrar nada e, para quem pode enviar, só registra e pergunta"""

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

    def test_contribuidor_recebe_a_pergunta_e_nada_e_baixado(self):
        """O get_file deste teste falha: o download só acontece depois da resposta"""

        profile = criar_profile_do_grupo('contrib', 'contributors')
        chat_vinculado(605, profile)

        texto = self.responder(update_de_foto(605))

        self.assertIn('Treinar o modelo', texto)
        self.assertIn('Testar o modelo', texto)
        photo = TelegramPhoto.objects.get()
        self.assertEqual(photo.telegram_user.profile, profile)
        self.assertEqual(photo.purpose, '')
        self.assertFalse(photo.image)

    def test_administrador_tem_a_imagem_registrada(self):
        profile = criar_profile_do_grupo('adm', 'admins')
        chat_vinculado(606, profile)

        self.responder(update_de_foto(606))

        self.assertEqual(TelegramPhoto.objects.count(), 1)

    def test_album_aceito_pergunta_uma_vez_so(self):
        profile = criar_profile_do_grupo('contrib', 'contributors')
        chat_vinculado(608, profile)

        updates = [update_de_foto(608, media_group_id='alb2') for _ in range(3)]
        for update in updates:
            async_to_sync(self.bot._handle_photo)(update, self.context)

        self.assertEqual([u.message.reply_text.call_count for u in updates], [1, 0, 0])
        self.assertEqual(TelegramPhoto.objects.pending().count(), 3)

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


def update_de_texto(chat_id, texto):
    """Um update do python-telegram-bot com uma mensagem de texto"""

    message = Mock(text=texto, media_group_id=None)
    message.reply_text = RespostaFake()

    update = Mock(message=message)
    update.effective_chat.id = chat_id
    update.effective_user.first_name = 'Nome no Telegram'

    return update


@override_settings(AI_MEDIA_ROOT=TEMP_AI_MEDIA_ROOT)
class HandleEscolhaUsoTests(TestCase):
    """A resposta 1 ou 2 baixa as imagens pendentes para media-ia/training ou media-ia/test"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_AI_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        from telegram_bot.handlers import TelegramBot

        self.bot = TelegramBot.__new__(TelegramBot)
        self.bot._ultimo_album_recusado = {}

        self.baixados = []
        self.invalidos = set()

        test = self

        class ArquivoFake:
            def __init__(self, file_id):
                self.file_id = file_id

            async def download_as_bytearray(self):
                if self.file_id in test.invalidos:
                    return bytearray(b'nao sou imagem')
                return bytearray(make_image_bytes())

        async def get_file(file_id):
            test.baixados.append(file_id)
            return ArquivoFake(file_id)

        # Mensagens que o bot manda por conta própria (a citação "Imagem N")
        self.citacoes = []

        async def send_message(**kwargs):
            test.citacoes.append(kwargs)

        self.context = Mock()
        self.context.bot.get_file = get_file
        self.context.bot.send_message = send_message

        profile = criar_profile_do_grupo('contrib', 'contributors')
        chat_vinculado(700, profile)

    def pendentes(self, total, chat_id=700):
        for i in range(total):
            register_pending_photo(
                chat_id=chat_id, file_id='f{}'.format(i), file_unique_id='u{}'.format(i),
                telegram_message_id=50 + i,
            )

    def responder(self, texto):
        update = update_de_texto(700, texto)
        async_to_sync(self.bot._handle_text)(update, self.context)
        return update.message.reply_text.textos

    def test_resposta_1_grava_todas_em_training_e_pede_as_descricoes(self):
        self.pendentes(3)

        textos = self.responder('1')

        self.assertEqual(self.baixados, ['f0', 'f1', 'f2'])
        self.assertIn('3 imagens salvas para treinar o modelo', textos[0])
        self.assertIn('`1 - ', textos[0])
        for photo in TelegramPhoto.objects.all():
            self.assertEqual(photo.purpose, 'training')
            self.assertTrue(photo.image.name.startswith('training/pending/'))
            self.assertTrue(os.path.exists(photo.image.path))
            self.assertTrue(photo.awaiting_description)

        # Cada foto é citada com o seu número
        self.assertEqual(
            [(c['text'], c['reply_to_message_id']) for c in self.citacoes],
            [('📷 Imagem *1*', 50), ('📷 Imagem *2*', 51), ('📷 Imagem *3*', 52)],
        )
        self.assertTrue(all(c['chat_id'] == 700 for c in self.citacoes))

    def test_uma_imagem_pede_a_descricao_sem_numero(self):
        self.pendentes(1)

        textos = self.responder('1')

        self.assertIn('Imagem salva para treinar o modelo', textos[0])
        self.assertIn('qual é a planta', textos[0])
        self.assertEqual(self.citacoes, [])

    def test_descricao_unica_libera_para_aprovacao(self):
        self.pendentes(1)
        self.responder('1')

        textos = self.responder('Soja com manchas amarelas')

        self.assertIn('Descrição recebida', textos[0])
        self.assertIn('revisão de um administrador', textos[0])
        photo = TelegramPhoto.objects.get()
        self.assertEqual(photo.description, 'Soja com manchas amarelas')
        self.assertEqual(list(TelegramPhoto.objects.awaiting_approval()), [photo])

    def test_descricoes_parciais_dizem_o_que_falta(self):
        self.pendentes(3)
        self.responder('1')

        textos = self.responder('1 - Saudável\n3 - Ferrugem')

        self.assertIn('*2*', textos[0])
        self.assertIn('Ainda falta', textos[0])

        textos = self.responder('2 - Oídio')

        self.assertIn('Descrição recebida', textos[0])
        self.assertEqual(TelegramPhoto.objects.awaiting_approval().count(), 3)

    def test_texto_sem_numero_com_varias_imagens_lembra_o_formato(self):
        self.pendentes(2)
        self.responder('1')

        textos = self.responder('Todas são soja')

        self.assertIn('*2* imagem(ns) de treino aguardando descrição', textos[0])
        self.assertIn('*1, 2*', textos[0])
        self.assertEqual(TelegramPhoto.objects.awaiting_description().count(), 2)

    def test_imagens_novas_no_meio_das_descricoes_perguntam_o_uso_primeiro(self):
        self.pendentes(1)
        self.responder('1')
        register_pending_photo(chat_id=700, file_id='nova', file_unique_id='nova', telegram_message_id=99)

        textos = self.responder('Soja saudável')

        self.assertIn('*1* imagem(ns) aguardando', textos[0])
        self.assertEqual(TelegramPhoto.objects.awaiting_description().count(), 1)

        textos = self.responder('1')

        # A antiga continua com o número 1 e a nova vira a 2
        self.assertIn('2 imagens salvas', textos[0])
        self.assertEqual(
            [(c['text'], c['reply_to_message_id']) for c in self.citacoes],
            [('📷 Imagem *1*', 50), ('📷 Imagem *2*', 99)],
        )

    def test_administrador_tambem_descreve_e_passa_pela_revisao(self):
        chat_vinculado(701, criar_profile_do_grupo('adm', 'admins'))
        self.pendentes(1, chat_id=701)

        update = update_de_texto(701, '1')
        async_to_sync(self.bot._handle_text)(update, self.context)
        texto = update.message.reply_text.textos[0]

        self.assertIn('qual é a planta', texto)
        photo = TelegramPhoto.objects.get(telegram_user__chat_id=701)
        self.assertTrue(photo.image.name.startswith('training/pending/'))
        self.assertIsNone(photo.reviewed_at)
        self.assertTrue(photo.awaiting_description)

    def test_resposta_2_grava_em_test(self):
        self.pendentes(1)

        textos = self.responder(' 2 ')

        self.assertIn('salva(s) para testar o modelo', textos[0])
        self.assertNotIn('revisão', textos[0])
        photo = TelegramPhoto.objects.get()
        self.assertEqual(photo.purpose, 'test')
        self.assertTrue(photo.image.name.startswith('test/'))

    def test_outro_texto_lembra_a_pergunta_e_nao_baixa(self):
        self.pendentes(2)

        textos = self.responder('treinar')

        self.assertIn('*2* imagem(ns) aguardando', textos[0])
        self.assertEqual(self.baixados, [])
        self.assertEqual(TelegramPhoto.objects.pending().count(), 2)

    def test_imagem_invalida_e_descartada_e_o_resto_e_salvo(self):
        self.pendentes(3)
        self.invalidos = {'f1'}

        textos = self.responder('1')

        self.assertIn('2 imagens salvas', textos[0])
        self.assertIn('1 imagem(ns) não puderam ser salvas', textos[0])
        self.assertEqual(TelegramPhoto.objects.count(), 2)
        self.assertEqual(TelegramPhoto.objects.pending().count(), 0)

    def test_sem_pendentes_o_numero_recebe_a_ajuda(self):
        textos = self.responder('1')

        self.assertIn('Não entendi', textos[0])
        self.assertEqual(self.baixados, [])

    def test_segunda_resposta_nao_regrava(self):
        self.pendentes(1)

        self.responder('1')
        self.responder('Soja saudável')
        textos = self.responder('2')

        self.assertIn('Não entendi', textos[0])
        self.assertEqual(TelegramPhoto.objects.get().purpose, 'training')


@override_settings(AI_MEDIA_ROOT=TEMP_AI_MEDIA_ROOT)
class TelegramPhotoAdminTests(TestCase):
    """media-ia/ não tem URL pública: o admin entrega o arquivo por rota própria"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_AI_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        pendente, _ = register_pending_photo(chat_id=800, file_unique_id='adm')
        self.photo = store_photo_file(pendente.pk, make_image_bytes(), 'training')
        self.url = '/admin/telegram_bot/telegramphoto/{}/arquivo/'.format(self.photo.pk)

    def test_equipe_ve_o_arquivo_e_a_pagina_do_registro(self):
        User.objects.create_superuser('adm', 'adm@exemplo.com', 'senha-de-teste')
        self.client.login(username='adm', password='senha-de-teste')

        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(b''.join(resposta.streaming_content), make_image_bytes())

        pagina = self.client.get('/admin/telegram_bot/telegramphoto/{}/change/'.format(self.photo.pk))
        self.assertContains(pagina, self.url)
        self.assertContains(pagina, 'media-ia/training/')

    def test_anonimo_nao_ve_o_arquivo(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 302)


class BotRoleTests(TestCase):
    """Qual ajuda cada conta recebe, pelas permissões"""

    def test_chat_desconhecido(self):
        self.assertEqual(bot_role(900), (BotRole.UNLINKED, ''))

    def test_chat_sem_conta_vinculada(self):
        TelegramUser.objects.create(chat_id=901)

        self.assertEqual(bot_role(901).role, BotRole.UNLINKED)

    def test_usuario_comum(self):
        chat_vinculado(902, criar_profile_do_grupo('comum', 'common_users', nome='Ana'))

        self.assertEqual(bot_role(902), (BotRole.COMMON, 'Ana'))

    def test_contribuidor(self):
        chat_vinculado(903, criar_profile_do_grupo('contrib', 'contributors'))

        self.assertEqual(bot_role(903).role, BotRole.CONTRIBUTOR)

    def test_administrador(self):
        chat_vinculado(904, criar_profile_do_grupo('adm', 'admins'))

        self.assertEqual(bot_role(904).role, BotRole.ADMIN)

    def test_superusuario_e_administrador(self):
        profile = criar_profile('root', 'root@exemplo.com')
        profile.user.is_superuser = True
        profile.user.save()
        chat_vinculado(905, profile)

        self.assertEqual(bot_role(905).role, BotRole.ADMIN)

    def test_administrador_desativado_vira_comum(self):
        profile = criar_profile_do_grupo('adm', 'admins')
        profile.user.is_active = False
        profile.user.save()
        chat_vinculado(906, profile)

        self.assertEqual(bot_role(906).role, BotRole.COMMON)


class HandleAjudaTests(TestCase):
    """Toda mensagem não prevista recebe a ajuda do tipo de conta, chamando pelo nome"""

    def setUp(self):
        from telegram_bot.handlers import TelegramBot

        self.bot = TelegramBot.__new__(TelegramBot)
        self.bot._ultimo_album_recusado = {}
        self.context = Mock()

    def texto(self, chat_id, texto='oi'):
        update = update_de_texto(chat_id, texto)
        async_to_sync(self.bot._handle_text)(update, self.context)
        return update.message.reply_text.textos

    def geral(self, update):
        async_to_sync(self.bot._handle_any_message)(update, self.context)
        return update.message.reply_text.textos

    def test_nao_vinculado_usa_o_nome_do_telegram_e_explica_o_vinculo(self):
        texto = self.texto(910)[0]

        self.assertIn('Olá, Nome no Telegram!', texto)
        self.assertIn('Não entendi', texto)
        self.assertIn(site_url('dashboard:profile'), texto)

    def test_comum_ve_alertas_e_como_virar_contribuidor(self):
        chat_vinculado(911, criar_profile_do_grupo('comum', 'common_users', nome='Ana Comum'))

        texto = self.texto(911)[0]

        self.assertIn('Olá, Ana Comum!', texto)
        self.assertIn('/stop', texto)
        self.assertIn(site_url('dashboard:solicitation'), texto)
        self.assertNotIn('treinar', texto)

    def test_contribuidor_ve_o_envio_de_imagens(self):
        chat_vinculado(912, criar_profile_do_grupo('contrib', 'contributors', nome='Caio'))

        texto = self.texto(912)[0]

        self.assertIn('Olá, Caio!', texto)
        self.assertIn('*contribuidor*', texto)
        self.assertIn('*treinar* (1)', texto)
        self.assertNotIn(site_url('dashboard:solicitation_list'), texto)
        self.assertNotIn(site_url('dashboard:ai_model_review'), texto)

    def test_administrador_ve_tambem_a_revisao_de_pedidos(self):
        chat_vinculado(913, criar_profile_do_grupo('adm', 'admins', nome='Bia'))

        texto = self.texto(913)[0]

        self.assertIn('Olá, Bia!', texto)
        self.assertIn('*administrador*', texto)
        self.assertIn('*treinar* (1)', texto)
        self.assertIn(site_url('dashboard:solicitation_list'), texto)
        self.assertIn(site_url('dashboard:ai_model_review'), texto)
        self.assertIn('categorizadas', texto)
        self.assertNotIn('já entram aprovadas', texto)

    def test_nome_com_caractere_de_markdown_e_escapado(self):
        chat_vinculado(914, criar_profile_do_grupo('x', 'common_users', nome='joao_pedro'))

        self.assertIn('Olá, joao\\_pedro!', self.texto(914)[0])

    def test_comando_desconhecido_recebe_a_ajuda(self):
        chat_vinculado(915, criar_profile_do_grupo('contrib', 'contributors', nome='Caio'))

        texto = self.geral(update_de_texto(915, '/inexistente'))[0]

        self.assertIn('Não entendi', texto)
        self.assertIn('*contribuidor*', texto)

    def test_figurinha_recebe_a_ajuda(self):
        chat_vinculado(916, criar_profile_do_grupo('comum', 'common_users'))

        textos = self.geral(update_de_texto(916, None))

        self.assertEqual(len(textos), 1)

    def test_album_de_videos_recebe_uma_ajuda_so(self):
        updates = [update_de_texto(917, None) for _ in range(3)]
        for update in updates:
            update.message.media_group_id = 'videos'

        respostas = [len(self.geral(update)) for update in updates]

        self.assertEqual(respostas, [1, 0, 0])

    def test_update_sem_mensagem_e_ignorado(self):
        update = Mock(message=None)

        async_to_sync(self.bot._handle_any_message)(update, self.context)

    def test_comando_ajuda_nao_diz_que_nao_entendeu(self):
        chat_vinculado(918, criar_profile_do_grupo('comum', 'common_users', nome='Ana'))
        update = update_de_texto(918, '/ajuda')

        async_to_sync(self.bot._handle_help)(update, self.context)

        texto = update.message.reply_text.textos[0]
        self.assertIn('Olá, Ana!', texto)
        self.assertNotIn('Não entendi', texto)
