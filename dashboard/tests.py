import tempfile
from io import BytesIO

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import Profile
# Atenção: os *Solicitation vivos são os de dashboard.models (o pacote
# dashboard/models/ tem precedência sobre dashboard/models.py). As classes de
# mesmo nome em accounts/models/ estão comentadas no __init__ e nunca chegam a
# ser registradas no app registry — são código morto.
from dashboard.models import (
    DiseasePhotoSolicitation, DiseaseSolicitation, PhotoSolicitation, PlantSolicitation,
)
from disease.models import Culture, Disease, PhotoDisease
from disease.tests import criar_doenca
from herbarium.models import Family, Photo, Plant, Region
from herbarium.tests import criar_planta


DADOS_CADASTRO = {
    'username': 'teste1',
    'email': 'teste1@exemplo.com',
    'password1': 'SenhaForte!2026',
    'password2': 'SenhaForte!2026',
    'name': 'Teste Um',
    'institution': 'IFRS',
    'role': 'Aluno',
    'phone': '54999990000',
    'cpf': '12345678901',
    'rg': '1234567890',
}


class CreateUserViewTests(TestCase):
    """Cadastro em /painel/criar/.

    O post_save de accounts/signals.py já cria um Profile em branco; a view
    precisa reaproveitá-lo em vez de criar um segundo, senão o OneToOne estoura.
    """

    def setUp(self):
        self.url = reverse('dashboard:create')

    def test_cadastro_valido_redireciona(self):
        response = self.client.post(self.url, DADOS_CADASTRO)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='teste1').exists())

    def test_cria_exatamente_um_profile(self):
        self.client.post(self.url, DADOS_CADASTRO)

        user = User.objects.get(username='teste1')
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)

    def test_profile_fica_com_os_dados_do_formulario(self):
        """Não pode sobrar o Profile em branco criado pelo signal"""
        self.client.post(self.url, DADOS_CADASTRO)

        profile = User.objects.get(username='teste1').profile
        self.assertEqual(profile.name, 'Teste Um')
        self.assertEqual(profile.cpf, '12345678901')
        self.assertEqual(profile.institution, 'IFRS')

    def test_novo_usuario_entra_em_common_users(self):
        self.client.post(self.url, DADOS_CADASTRO)

        user = User.objects.get(username='teste1')
        self.assertIn('common_users', user.groups.values_list('name', flat=True))

    def test_email_repetido_vira_erro_de_formulario(self):
        self.client.post(self.url, DADOS_CADASTRO)

        outro = dict(DADOS_CADASTRO, username='teste2', email='TESTE1@EXEMPLO.COM',
                     phone='54999990001', cpf='98765432100')
        response = self.client.post(self.url, outro)

        # Reexibe o formulário com erro em vez de estourar IntegrityError
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='teste2').exists())


# ---------------------------------------------------------------------------
# Envio e aprovação de fotos: quem pode o quê
# ---------------------------------------------------------------------------

def imagem(largura=1920, altura=1080, nome='foto.jpg'):
    """Upload de imagem com a resolução pedida"""

    buffer = BytesIO()
    Image.new('RGB', (largura, altura), color='green').save(buffer, 'JPEG')

    return SimpleUploadedFile(nome, buffer.getvalue(), content_type='image/jpeg')


def imagem_full_hd(nome='foto.jpg'):
    """Upload no tamanho mínimo aceito — 1920x1080"""

    return imagem(nome=nome)


def foto_no_disco(model, published=False, **campos):
    """Cria uma foto com arquivo de verdade em MEDIA_ROOT.

    Os helpers de herbarium/tests.py e disease/tests.py usam bulk_create e gravam
    só a linha no banco — o suficiente para testar `published`, mas não aqui:
    aprovar chama Photo.save(), que reabre a imagem com o Pillow e estoura
    FileNotFoundError se o arquivo não existir.

    O `published` vai por update() para não passar de novo pelo save().
    """

    foto = model(image=imagem_full_hd(), **campos)
    foto.save()

    model.objects.filter(pk=foto.pk).update(published=published)
    foto.refresh_from_db()

    return foto


def usuario_do_grupo(username, grupo):
    """Cria um usuário já dentro de um dos três grupos padrão"""

    user = User.objects.create_user(username, '{}@exemplo.com'.format(username), 'senha-de-teste')
    user.groups.add(Group.objects.get(name=grupo))

    return user


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PlantPhotoUploadPermissionTests(TestCase):
    """/painel/solicitacao-de-foto-planta/ — só contribuidor e administrador enviam"""

    def setUp(self):
        self.url = reverse('dashboard:photo_solicitation')
        self.plant = criar_planta()

    def dados(self):
        return {'plant': self.plant.pk, 'image': imagem_full_hd()}

    def test_anonimo_vai_para_o_login(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resposta.url)

    def test_usuario_comum_recebe_403(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(Photo.objects.exists())
        self.assertFalse(PhotoSolicitation.objects.exists())

    def test_contribuidor_envia_e_a_foto_nasce_pendente(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(resposta.status_code, 302)

        foto = Photo.objects.get()
        # O ponto do commit=False: antes, published ficava NULL
        self.assertIs(foto.published, False)
        self.assertFalse(self.plant.published_photos.exists())

    def test_contribuidor_gera_solicitacao_em_analise(self):
        user = usuario_do_grupo('contrib', 'contributors')
        self.client.force_login(user)

        self.client.post(self.url, self.dados())

        solicitacao = PhotoSolicitation.objects.get()
        self.assertEqual(solicitacao.user, user)
        self.assertEqual(solicitacao.status, PhotoSolicitation.Status.SENT)

    def test_administrador_tambem_envia(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(resposta.status_code, 302)
        self.assertIs(Photo.objects.get().published, False)


class PlantSolicitationPermissionTests(TestCase):
    """/painel/solicitacao-de-planta/ — só contribuidor e administrador pedem planta nova"""

    def setUp(self):
        self.url = reverse('dashboard:plant_solicitation')
        self.familia = Family.objects.create(name='Poaceae')

    def dados(self):
        return {
            'name': 'Azevém',
            'scientific_name': 'Lolium multiflorum',
            'family': self.familia.pk,
            'description': 'descrição',
            'importance': 'importância',
            # Criada pela migração herbarium/0002_seed_regions
            'occurrence_regions': [Region.objects.get(name='Sul').pk],
        }

    def test_anonimo_vai_para_o_login(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resposta.url)

    def test_anonimo_nao_cria_planta(self):
        self.client.post(self.url, self.dados())

        self.assertFalse(Plant.objects.exists())

    def test_usuario_comum_nao_abre_o_formulario(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_usuario_comum_recebe_403_e_nada_e_criado(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(Plant.objects.exists())
        self.assertFalse(PlantSolicitation.objects.exists())

    def test_contribuidor_gera_solicitacao_em_analise(self):
        user = usuario_do_grupo('contrib', 'contributors')
        self.client.force_login(user)

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(resposta.status_code, 302)
        solicitacao = PlantSolicitation.objects.get()
        self.assertEqual(solicitacao.user, user)
        self.assertEqual(solicitacao.status, PlantSolicitation.Status.SENT)
        self.assertEqual(solicitacao.new_plant.name, 'Azevém')

    def test_administrador_tambem_solicita(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(PlantSolicitation.objects.exists())


class GestaoDoAcervoMixin:
    """Base dos testes de edição, exclusão e revisão de planta/doença.

    Até 24/09/2026 estas views não tinham verificação nenhuma: um visitante anônimo
    editava e apagava plantas e doenças (com as fotos, em cascata). Cada subclasse
    declara `rotas()` — (método, nome da rota, args) — e os testes abaixo cobrem
    todas elas para cada papel.
    """

    def rotas(self):
        raise NotImplementedError

    def estado_intacto(self):
        """True se nada foi apagado nem alterado"""
        raise NotImplementedError

    def chamar(self, metodo, nome, args):
        return getattr(self.client, metodo)(reverse(nome, args=args))

    def test_anonimo_vai_para_o_login_e_nada_muda(self):
        for metodo, nome, args in self.rotas():
            with self.subTest(rota=nome, metodo=metodo):
                resposta = self.chamar(metodo, nome, args)

                self.assertEqual(resposta.status_code, 302)
                self.assertIn(reverse('dashboard:login'), resposta.url)
                self.assertTrue(self.estado_intacto())

    def test_usuario_comum_recebe_403_e_nada_muda(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        for metodo, nome, args in self.rotas():
            with self.subTest(rota=nome, metodo=metodo):
                self.assertEqual(self.chamar(metodo, nome, args).status_code, 403)
                self.assertTrue(self.estado_intacto())

    def test_contribuidor_recebe_403_e_nada_muda(self):
        """Contribuidor envia, mas não edita, apaga nem revisa"""

        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        for metodo, nome, args in self.rotas():
            with self.subTest(rota=nome, metodo=metodo):
                self.assertEqual(self.chamar(metodo, nome, args).status_code, 403)
                self.assertTrue(self.estado_intacto())


class PlantManagementPermissionTests(GestaoDoAcervoMixin, TestCase):
    """Editar, apagar e revisar planta: só administrador"""

    def setUp(self):
        self.plant = criar_planta('Buva')
        self.pendente = Plant.objects.create(
            name='Azevém', scientific_name='Lolium multiflorum',
            family=self.plant.family, description='d', importance='i',
        )
        self.solicitacao = PlantSolicitation.objects.create(
            user=usuario_do_grupo('autor', 'contributors'),
            status=PlantSolicitation.Status.SENT,
            new_plant=self.pendente,
        )

    def rotas(self):
        return [
            ('get', 'dashboard:plant_update', [self.plant.pk]),
            # POST com o nome alterado: prova que a edição não passa, não só a tela
            ('post', 'dashboard:plant_update', [self.plant.pk]),
            ('post', 'dashboard:delete_plant', [self.plant.slug]),
            ('get', 'dashboard:plant_solicitation_list', []),
            ('get', 'dashboard:detail-solicitation-plant', [self.solicitacao.pk]),
            ('post', 'dashboard:delete_plant_solicitation', [self.solicitacao.pk]),
        ]

    def chamar(self, metodo, nome, args):
        if nome == 'dashboard:plant_update' and metodo == 'post':
            return self.client.post(reverse(nome, args=args), {
                'name': 'NOME ADULTERADO', 'scientific_name': 'x',
                'family': self.plant.family.pk, 'description': 'x', 'importance': 'x',
                'occurrence_regions': [Region.objects.get(name='Sul').pk],
            })
        return super().chamar(metodo, nome, args)

    def estado_intacto(self):
        self.plant.refresh_from_db()
        return (self.plant.name == 'Buva'
                and PlantSolicitation.objects.filter(pk=self.solicitacao.pk).exists())

    def test_administrador_edita_a_planta(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:plant_update', args=[self.plant.pk])).status_code, 200)

    def test_administrador_apaga_a_planta(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.post(reverse('dashboard:delete_plant', args=[self.plant.slug]))

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Plant.objects.filter(pk=self.plant.pk).exists())

    def test_administrador_revisa_as_solicitacoes(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:plant_solicitation_list')).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('dashboard:detail-solicitation-plant', args=[self.solicitacao.pk])).status_code, 200)

    def test_administrador_recusa_solicitacao(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.post(reverse('dashboard:delete_plant_solicitation', args=[self.solicitacao.pk]))

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(PlantSolicitation.objects.filter(pk=self.solicitacao.pk).exists())

    def test_cada_linha_abre_o_proprio_modal_de_exclusao(self):
        """Antes todas as linhas abriam #exampleModal — o id repetido fazia o
        navegador usar sempre o primeiro, e 'Excluir' em qualquer planta pedia para
        confirmar a exclusão da primeira da lista."""

        self.pendente.published = True
        self.pendente.save()
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        html = self.client.get(reverse('dashboard:herbarium_update')).content.decode()

        for planta in (self.plant, self.pendente):
            self.assertEqual(html.count('id="exampleModal{}"'.format(planta.pk)), 1)
            self.assertIn('data-target="#exampleModal{}"'.format(planta.pk), html)
        self.assertNotIn('id="exampleModal"', html)


class DiseaseManagementPermissionTests(GestaoDoAcervoMixin, TestCase):
    """Editar, apagar e revisar doença: só administrador"""

    def setUp(self):
        self.disease = criar_doenca('Ferrugem')
        self.pendente = Disease.objects.create(
            name_disease='Oídio', scientific_name_disease='Erysiphe',
            culture_disease=self.disease.culture_disease, symptoms_disease='s',
        )
        self.solicitacao = DiseaseSolicitation.objects.create(
            user=usuario_do_grupo('autor', 'contributors'),
            status=DiseaseSolicitation.Status.SENT,
            new_disease=self.pendente,
        )

    def rotas(self):
        return [
            ('get', 'dashboard:disease_update', [self.disease.pk]),
            ('post', 'dashboard:delete_disease', [self.disease.slug]),
            ('get', 'dashboard:disease_solicitation_list', []),
            ('get', 'dashboard:detail-solicitation-disease', [self.solicitacao.pk]),
            ('post', 'dashboard:delete_diesase_solicitation', [self.solicitacao.pk]),
        ]

    def estado_intacto(self):
        return (Disease.objects.filter(pk=self.disease.pk).exists()
                and DiseaseSolicitation.objects.filter(pk=self.solicitacao.pk).exists())

    def test_administrador_edita_a_doenca(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:disease_update', args=[self.disease.pk])).status_code, 200)

    def test_administrador_apaga_a_doenca(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.post(reverse('dashboard:delete_disease', args=[self.disease.slug]))

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Disease.objects.filter(pk=self.disease.pk).exists())

    def test_administrador_revisa_e_recusa_solicitacao(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:disease_solicitation_list')).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('dashboard:detail-solicitation-disease', args=[self.solicitacao.pk])).status_code, 200)

        resposta = self.client.post(reverse('dashboard:delete_diesase_solicitation', args=[self.solicitacao.pk]))

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(DiseaseSolicitation.objects.filter(pk=self.solicitacao.pk).exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PlantPhotoApprovalPermissionTests(TestCase):
    """Aprovar foto de planta exige herbarium.approve_photo"""

    def setUp(self):
        self.plant = criar_planta()
        self.foto = foto_no_disco(Photo, plant=self.plant)
        self.solicitacao = PhotoSolicitation.objects.create(
            user=usuario_do_grupo('autor', 'contributors'),
            status=PhotoSolicitation.Status.SENT,
            new_photo=self.foto,
        )
        self.url = reverse('dashboard:accept_plant_photo', args=[self.solicitacao.pk])

    def test_contribuidor_nao_aprova(self):
        self.client.force_login(usuario_do_grupo('outro', 'contributors'))

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 403)
        self.foto.refresh_from_db()
        self.assertIs(self.foto.published, False)

    def test_usuario_comum_nao_aprova(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_administrador_aprova_e_a_foto_vai_ao_ar(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 302)
        self.foto.refresh_from_db()
        self.solicitacao.refresh_from_db()
        self.assertIs(self.foto.published, True)
        self.assertEqual(self.solicitacao.status, PhotoSolicitation.Status.ACCEPTED)
        self.assertIn(self.foto, self.plant.published_photos)

    def test_lista_de_revisao_e_so_de_quem_aprova(self):
        lista = reverse('dashboard:photo_solicitation_list')

        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))
        self.assertEqual(self.client.get(lista).status_code, 403)

        self.client.force_login(usuario_do_grupo('adm', 'admins'))
        self.assertEqual(self.client.get(lista).status_code, 200)

    def test_anonimo_nao_alcanca_a_lista_de_revisao(self):
        resposta = self.client.get(reverse('dashboard:photo_solicitation_list'))

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resposta.url)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DiseasePhotoPermissionTests(TestCase):
    """O mesmo contrato no herbário fitopatológico"""

    def setUp(self):
        self.disease = criar_doenca()
        self.envio = reverse('dashboard:disease_photo_solicitation')

    def dados(self):
        return {'disease': self.disease.pk, 'image': imagem_full_hd()}

    def test_usuario_comum_recebe_403(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        resposta = self.client.post(self.envio, self.dados())

        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(PhotoDisease.objects.exists())

    def test_contribuidor_envia_e_a_foto_nasce_pendente(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        resposta = self.client.post(self.envio, self.dados())

        self.assertEqual(resposta.status_code, 302)
        self.assertIs(PhotoDisease.objects.get().published, False)
        self.assertFalse(self.disease.published_photos.exists())

    def test_administrador_aprova(self):
        foto = foto_no_disco(PhotoDisease, disease=self.disease)
        solicitacao = DiseasePhotoSolicitation.objects.create(
            user=usuario_do_grupo('autor', 'contributors'),
            status=DiseasePhotoSolicitation.Status.SENT,
            new_photo=foto,
        )
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resposta = self.client.get(
            reverse('dashboard:accept_disease_photo', args=[solicitacao.pk])
        )

        self.assertEqual(resposta.status_code, 302)
        foto.refresh_from_db()
        self.assertIs(foto.published, True)

    def test_contribuidor_nao_aprova(self):
        foto = foto_no_disco(PhotoDisease, disease=self.disease)
        solicitacao = DiseasePhotoSolicitation.objects.create(
            user=usuario_do_grupo('autor', 'contributors'),
            status=DiseasePhotoSolicitation.Status.SENT,
            new_photo=foto,
        )
        self.client.force_login(usuario_do_grupo('outro', 'contributors'))

        resposta = self.client.get(
            reverse('dashboard:accept_disease_photo', args=[solicitacao.pk])
        )

        self.assertEqual(resposta.status_code, 403)
        foto.refresh_from_db()
        self.assertIs(foto.published, False)


class MenuPermissionTests(TestCase):
    """O painel não deve oferecer o que a view vai negar com 403"""

    def html(self, url):
        return self.client.get(url).content.decode()

    def test_usuario_comum_nao_ve_o_botao_de_enviar_foto_de_planta(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        self.assertNotIn('Adicionar uma foto de planta',
                         self.html(reverse('dashboard:herbarium_update')))

    def test_contribuidor_ve_o_botao_de_enviar_foto_de_planta(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        self.assertIn('Adicionar uma foto de planta',
                      self.html(reverse('dashboard:herbarium_update')))

    def test_usuario_comum_nao_ve_o_botao_de_solicitar_planta(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        html = self.html(reverse('dashboard:herbarium_update'))

        self.assertNotIn('Adicionar uma planta', html)
        self.assertNotIn(reverse('dashboard:plant_solicitation'), html)

    def test_contribuidor_ve_o_botao_de_solicitar_planta(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        self.assertIn('Adicionar uma planta',
                      self.html(reverse('dashboard:herbarium_update')))

    def test_usuario_comum_nao_ve_o_botao_de_enviar_foto_de_doenca(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        self.assertNotIn('Adicionar uma foto de doença',
                         self.html(reverse('dashboard:disease_update')))

    def test_contribuidor_ve_o_botao_de_enviar_foto_de_doenca(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        self.assertIn('Adicionar uma foto de doença',
                      self.html(reverse('dashboard:disease_update')))

    def test_contribuidor_nao_ve_o_menu_de_aprovacao(self):
        """A lista de revisão responde 403 a ele; o link não pode aparecer"""

        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        self.assertNotIn(reverse('dashboard:photo_solicitation_list'),
                         self.html(reverse('dashboard:herbarium_update')))

    def test_administrador_ve_o_menu_de_aprovacao(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        html = self.html(reverse('dashboard:herbarium_update'))

        self.assertIn(reverse('dashboard:photo_solicitation_list'), html)
        self.assertIn(reverse('dashboard:disease_photo_solicitation_list'), html)

    def test_usuario_comum_so_ve_o_pedido_de_contribuidor(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        html = self.html(reverse('dashboard:herbarium_update'))

        self.assertIn(reverse('dashboard:solicitation'), html)
        self.assertNotIn(reverse('dashboard:photo_solicitation'), html)


class TemplateCommentTests(TestCase):
    """Comentário de template não pode vazar para a tela.

    `{# ... #}` é comentário de uma linha só. Se quebrar linha, o Django não o
    reconhece como tag e imprime o texto cru na página — foi o que aconteceu com
    duas anotações no sidebar. Para várias linhas, use {% comment %}.
    """

    def paginas(self):
        return [
            reverse('dashboard:herbarium_update'),
            reverse('dashboard:disease_update'),
            reverse('dashboard:view_dashboard'),
        ]

    def test_nenhuma_marca_de_comentario_chega_ao_html(self):
        # Como administrador, para que o sidebar renderize o máximo de seções
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        for url in self.paginas():
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()

                self.assertNotIn('{#', html)
                self.assertNotIn('#}', html)

    def test_o_texto_dos_comentarios_nao_aparece(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        for url in self.paginas():
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()

                self.assertNotIn('add_manualalert', html)
                self.assertNotIn('MathModel está no app alerts', html)
                self.assertNotIn('Aprovar foto deixou de depender', html)


class ResolucaoMinimaTests(TestCase):
    """A imagem só é aceita a partir de 1920x1080 — core/validators.py"""

    def setUp(self):
        self.url = reverse('dashboard:photo_solicitation')
        self.plant = criar_planta()
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

    def enviar(self, largura, altura):
        return self.client.post(
            self.url, {'plant': self.plant.pk, 'image': imagem(largura, altura)}
        )

    def test_imagem_pequena_e_recusada_sem_gravar_nada(self):
        resposta = self.enviar(800, 600)

        # 200 = o formulário voltou com erro, e não 302 de sucesso nem 500
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Photo.objects.exists())
        self.assertFalse(PhotoSolicitation.objects.exists())

    def test_o_erro_aparece_no_campo_da_imagem(self):
        resposta = self.enviar(800, 600)

        erros = resposta.context['photo_form'].errors

        self.assertIn('image', erros)
        self.assertIn('1920x1080', str(erros['image']))

    def test_a_mensagem_diz_qual_era_a_resolucao_enviada(self):
        """Sem isso o contribuidor não sabe o quanto faltou"""

        resposta = self.enviar(1280, 720)

        self.assertIn('1280x720', str(resposta.context['photo_form'].errors['image']))

    def test_exatamente_full_hd_passa(self):
        """O mínimo é inclusivo"""

        resposta = self.enviar(1920, 1080)

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Photo.objects.count(), 1)

    def test_maior_que_full_hd_passa(self):
        resposta = self.enviar(2560, 1440)

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Photo.objects.count(), 1)

    def test_so_uma_das_dimensoes_pequena_ja_recusa(self):
        for largura, altura in [(1920, 1079), (1919, 1080)]:
            with self.subTest(largura=largura, altura=altura):
                Photo.objects.all().delete()

                self.assertEqual(self.enviar(largura, altura).status_code, 200)
                self.assertFalse(Photo.objects.exists())


class ResolucaoMinimaDoencaTests(TestCase):
    """O mesmo contrato no herbário fitopatológico"""

    def setUp(self):
        self.url = reverse('dashboard:disease_photo_solicitation')
        self.disease = criar_doenca()
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

    def enviar(self, largura, altura):
        return self.client.post(
            self.url, {'disease': self.disease.pk, 'image': imagem(largura, altura)}
        )

    def test_imagem_pequena_e_recusada(self):
        resposta = self.enviar(800, 600)

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(PhotoDisease.objects.exists())

    def test_full_hd_passa(self):
        resposta = self.enviar(1920, 1080)

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(PhotoDisease.objects.count(), 1)


class ResolucaoMinimaNoAdminTests(TestCase):
    """O /admin/ usa ModelForm próprio; o validador de campo cobre ele também"""

    def test_full_clean_recusa_imagem_pequena(self):
        from django.core.exceptions import ValidationError

        foto = Photo(plant=criar_planta(), image=imagem(640, 480), published=False)

        with self.assertRaises(ValidationError) as contexto:
            foto.full_clean()

        self.assertIn('image', contexto.exception.error_dict)

    def test_full_clean_aceita_full_hd(self):
        # published explícito: o campo é null=True mas não blank=True, então o
        # full_clean() o exige. Nada a ver com a resolução.
        foto = Photo(plant=criar_planta(), image=imagem_full_hd(), published=False)

        foto.full_clean()  # não pode levantar


class GestaoConteudoSemLoginTests(TestCase):
    """Culturas, publicações e detalhes de usuário: fechados a anônimo e comum.

    Até 24/09/2026 estas views não verificavam nada — um visitante anônimo
    editava, listava, via e apagava. Apagar uma cultura é o pior caso: cascateia
    sobre as doenças e as fotos delas. Ver seção 2.9/5.6 do balanço.
    """

    def setUp(self):
        # Doença pendurada na cultura: é o que a cascata apagaria junto
        self.cultura = Culture.objects.create(name='Trigo')
        self.doenca = Disease.objects.create(
            name_disease='Brusone', scientific_name_disease='Pyricularia oryzae',
            culture_disease=self.cultura, symptoms_disease='s', published_disease=True,
        )
        # Conta-alvo dos testes de exposição de dados; o Profile nasce pelo signal
        self.admin_user = User.objects.create_superuser('alvo', 'alvo@exemplo.com', 'senha-de-teste')

    def acervo_intacto(self):
        return (Culture.objects.filter(pk=self.cultura.pk).exists()
                and Disease.objects.filter(pk=self.doenca.pk).exists())

    # --- Culturas ---

    def test_anonimo_nao_apaga_cultura_nem_as_doencas_dela(self):
        resp = self.client.post(reverse('dashboard:delete_culture', args=[self.cultura.slug]))

        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)
        self.assertTrue(self.acervo_intacto())

    def test_usuario_comum_nao_apaga_cultura(self):
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        resp = self.client.post(reverse('dashboard:delete_culture', args=[self.cultura.slug]))

        self.assertEqual(resp.status_code, 403)
        self.assertTrue(self.acervo_intacto())

    def test_contribuidor_nao_apaga_cultura(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        resp = self.client.post(reverse('dashboard:delete_culture', args=[self.cultura.slug]))

        self.assertEqual(resp.status_code, 403)
        self.assertTrue(self.acervo_intacto())

    def test_anonimo_e_comum_nao_editam_nem_listam_cultura(self):
        rotas = [
            ('get', 'dashboard:culture_update', [self.cultura.pk]),
            ('get', 'dashboard:culture_solicitation', []),
            ('get', 'dashboard:culture_list', []),
        ]
        for metodo, nome, args in rotas:
            with self.subTest(rota=nome):
                # anônimo → login
                resp = getattr(self.client, metodo)(reverse(nome, args=args))
                self.assertEqual(resp.status_code, 302)
                self.assertIn(reverse('dashboard:login'), resp.url)

        self.client.force_login(usuario_do_grupo('comum', 'common_users'))
        for metodo, nome, args in rotas:
            with self.subTest(rota=nome, papel='comum'):
                self.assertEqual(getattr(self.client, metodo)(reverse(nome, args=args)).status_code, 403)

    def test_administrador_gerencia_cultura(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:culture_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:culture_update', args=[self.cultura.pk])).status_code, 200)

    def test_administrador_apaga_cultura(self):
        """Continua possível para quem deve — e a cascata é real, por isso o risco"""

        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        resp = self.client.post(reverse('dashboard:delete_culture', args=[self.cultura.slug]))

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Culture.objects.filter(pk=self.cultura.pk).exists())
        self.assertFalse(Disease.objects.filter(pk=self.doenca.pk).exists())

    # --- Publicações ---

    def test_anonimo_e_comum_nao_criam_editam_nem_apagam_publicacao(self):
        from core.models import Publication
        pub = Publication.objects.create(title='Aviso', content='texto')
        rotas = [
            ('get', 'dashboard:publication_add', []),
            ('get', 'dashboard:publication_photo_add', []),
            ('get', 'dashboard:publication_update', [pub.pk]),
            ('post', 'dashboard:delete_publication', [pub.pk]),
        ]
        for metodo, nome, args in rotas:
            with self.subTest(rota=nome, papel='anonimo'):
                resp = getattr(self.client, metodo)(reverse(nome, args=args))
                self.assertEqual(resp.status_code, 302)
                self.assertIn(reverse('dashboard:login'), resp.url)
                self.assertTrue(Publication.objects.filter(pk=pub.pk).exists())

        self.client.force_login(usuario_do_grupo('comum', 'common_users'))
        for metodo, nome, args in rotas:
            with self.subTest(rota=nome, papel='comum'):
                self.assertEqual(getattr(self.client, metodo)(reverse(nome, args=args)).status_code, 403)
                self.assertTrue(Publication.objects.filter(pk=pub.pk).exists())

    def test_administrador_gerencia_publicacao(self):
        from core.models import Publication
        pub = Publication.objects.create(title='Aviso', content='texto')
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:publication_add')).status_code, 200)
        resp = self.client.post(reverse('dashboard:delete_publication', args=[pub.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Publication.objects.filter(pk=pub.pk).exists())

    # --- Exclusão de conta e de pedido de contribuidor ---

    def test_anonimo_e_comum_nao_apagam_perfil(self):
        from accounts.models import Profile
        profile = Profile.objects.get(user=self.admin_user)
        url = reverse('dashboard:delete_user', args=[profile.pk])

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)
        self.assertTrue(Profile.objects.filter(pk=profile.pk).exists())

        self.client.force_login(usuario_do_grupo('comum', 'common_users'))
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Profile.objects.filter(pk=profile.pk).exists())

    def test_anonimo_nao_apaga_pedido_de_contribuidor(self):
        from accounts.models import Solicitation
        pedido = Solicitation.objects.create(user=usuario_do_grupo('pede', 'common_users'))

        resp = self.client.post(reverse('dashboard:delete_solicitation', args=[pedido.pk]))

        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)
        self.assertTrue(Solicitation.objects.filter(pk=pedido.pk).exists())

    # --- Detalhes de usuário (exposição de dados de contato) ---

    def test_anonimo_nao_ve_detalhes_de_usuario(self):
        from accounts.models import Profile
        profile = Profile.objects.get(user=self.admin_user)

        resp = self.client.get(reverse('dashboard:detail-user', args=[profile.pk]))

        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)

    def test_usuario_comum_nao_ve_detalhes_nem_lista_de_usuarios(self):
        from accounts.models import Profile
        profile = Profile.objects.get(user=self.admin_user)
        self.client.force_login(usuario_do_grupo('comum', 'common_users'))

        self.assertEqual(self.client.get(reverse('dashboard:detail-user', args=[profile.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('dashboard:user_list')).status_code, 403)

    def test_administrador_ve_lista_de_usuarios(self):
        self.client.force_login(usuario_do_grupo('adm', 'admins'))

        self.assertEqual(self.client.get(reverse('dashboard:user_list')).status_code, 200)

    # --- Oráculo de senha ---

    def test_anonimo_nao_usa_checar_senha(self):
        resp = self.client.post(reverse('dashboard:term_check_password'),
                                {'user': self.admin_user.pk, 'password': 'x'})

        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)


class GravacaoSemPermissaoTests(TestCase):
    """Views que gravam dados: nada é criado sem login e permissão"""

    def test_solicitacao_de_doenca_fechada_a_anonimo_e_comum(self):
        url = reverse('dashboard:disease_solicitation')
        cultura = Culture.objects.create(name='Aveia')
        dados = {'name_disease': 'Mancha', 'scientific_name_disease': 'X',
                 'culture_disease': cultura.pk, 'symptoms_disease': 's'}

        resp = self.client.post(url, dados)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)

        self.client.force_login(usuario_do_grupo('comum', 'common_users'))
        self.assertEqual(self.client.post(url, dados).status_code, 403)

        self.assertFalse(Disease.objects.filter(name_disease='Mancha').exists())
        self.assertFalse(DiseaseSolicitation.objects.exists())

    def test_contribuidor_ainda_abre_a_solicitacao_de_doenca(self):
        self.client.force_login(usuario_do_grupo('contrib', 'contributors'))

        self.assertEqual(self.client.get(reverse('dashboard:disease_solicitation')).status_code, 200)

    def test_leitura_de_sensor_humano_fechada_a_anonimo_e_comum(self):
        from alerts.models import Reading
        url = reverse('dashboard:sensor_human_add', args=[1])
        antes = Reading.objects.count()

        resp = self.client.post(url, {'choice': 'on', 'time': '2026-09-24 10:00'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard:login'), resp.url)

        self.client.force_login(usuario_do_grupo('adm', 'admins'))
        # Nem administrador: a gestão de alertas é só de superusuário
        self.assertEqual(self.client.post(url, {'choice': 'on'}).status_code, 403)

        self.assertEqual(Reading.objects.count(), antes)
