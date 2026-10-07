from django.contrib.auth.models import Group, Permission, User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.forms import ProfileForm, UserForm, UserUpdateForm
from accounts.models import Profile, normalize_telegram_username
from accounts.permissions import (
    ADMIN_PERMISSIONS,
    CONTRIBUTOR_PERMISSIONS,
    DEFAULT_GROUPS,
    GROUP_PERMISSIONS,
    ensure_default_groups,
)


DADOS_VALIDOS = {
    'username': 'novo',
    'email': 'novo@exemplo.com',
    'password1': 'SenhaForte!2026',
    'password2': 'SenhaForte!2026',
}


class UniqueEmailFormTests(TestCase):
    """O e-mail identifica a conta na recuperação de senha, então precisa ser único"""

    def setUp(self):
        self.existente = User.objects.create_user('ana', 'ana@exemplo.com', 'x')

    def test_rejeita_email_ja_usado(self):
        form = UserForm(dict(DADOS_VALIDOS, email='ana@exemplo.com'))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_rejeita_email_ja_usado_com_outro_case(self):
        form = UserForm(dict(DADOS_VALIDOS, email='ANA@Exemplo.COM'))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_aceita_email_livre(self):
        form = UserForm(DADOS_VALIDOS)

        self.assertTrue(form.is_valid(), form.errors)

    def test_edicao_aceita_o_proprio_email(self):
        form = UserUpdateForm(
            {'username': 'ana', 'email': 'ana@exemplo.com'}, instance=self.existente
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_edicao_rejeita_email_de_outra_conta(self):
        User.objects.create_user('bia', 'bia@exemplo.com', 'x')

        form = UserUpdateForm(
            {'username': 'ana', 'email': 'bia@exemplo.com'}, instance=self.existente
        )

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_dashboard_e_accounts_usam_a_mesma_classe(self):
        """Trava a divergência: create_user importa o UserForm de dashboard.forms"""
        from dashboard.forms import UserForm as DashboardUserForm
        from dashboard.forms import ProfileForm as DashboardProfileForm
        from accounts.forms import ProfileForm

        self.assertIs(DashboardUserForm, UserForm)
        self.assertIs(DashboardProfileForm, ProfileForm)


class UniqueEmailDatabaseTests(TestCase):
    """Garantia de banco, além da validação de formulário"""

    def test_banco_rejeita_email_duplicado_ignorando_case(self):
        User.objects.create_user('ana', 'ana@exemplo.com', 'x')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user('bia', 'ANA@EXEMPLO.COM', 'x')

    def test_banco_permite_varias_contas_sem_email(self):
        """O índice é parcial de propósito: createsuperuser pode não ter e-mail"""
        with transaction.atomic():
            User.objects.create_user('sem1', '', 'x')
            User.objects.create_user('sem2', '', 'x')

        self.assertEqual(User.objects.filter(email='').count(), 2)


DADOS_PERFIL = {
    'name': 'Ana Silva',
    'institution': 'IFRS',
    'role': 'Pesquisadora',
    'cpf': '12345678901',
    'rg': '1234567890',
}


class TelegramUsernameFormTests(TestCase):
    """O @ do Telegram é a chave do vínculo com o bot: opcional, mas único"""

    def setUp(self):
        self.ana = User.objects.create_user('ana', 'ana@exemplo.com', 'x')
        self.perfil_ana = Profile.objects.get(user=self.ana)

    def form(self, telegram_username, instance=None):
        dados = dict(DADOS_PERFIL, telegram_username=telegram_username)
        return ProfileForm(dados, instance=instance)

    def test_campo_em_branco_e_aceito(self):
        form = self.form('')

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['telegram_username'])

    def test_normaliza_arroba_e_maiusculas(self):
        form = self.form('@Ana_TG')

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['telegram_username'], 'ana_tg')

    def test_aceita_o_link_do_perfil(self):
        form = self.form('https://t.me/Ana_TG')

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['telegram_username'], 'ana_tg')

    def test_rejeita_formato_invalido(self):
        form = self.form('ana silva!')

        self.assertFalse(form.is_valid())
        self.assertIn('telegram_username', form.errors)

    def test_rejeita_arroba_ja_usado_por_outra_conta(self):
        self.perfil_ana.telegram_username = 'ana_tg'
        self.perfil_ana.save()

        bia = User.objects.create_user('bia', 'bia@exemplo.com', 'x')
        form = self.form('@ANA_TG', instance=Profile.objects.get(user=bia))

        self.assertFalse(form.is_valid())
        self.assertIn('telegram_username', form.errors)

    def test_edicao_aceita_o_proprio_arroba(self):
        self.perfil_ana.telegram_username = 'ana_tg'
        self.perfil_ana.save()

        form = self.form('ana_tg', instance=self.perfil_ana)

        self.assertTrue(form.is_valid(), form.errors)

    def test_save_normaliza_fora_do_formulario(self):
        """Admin e shell também precisam gravar a forma canônica"""
        self.perfil_ana.telegram_username = '  @Ana_TG '
        self.perfil_ana.save()
        self.perfil_ana.refresh_from_db()

        self.assertEqual(self.perfil_ana.telegram_username, 'ana_tg')

    def test_vazio_vira_null_para_nao_colidir_no_unique(self):
        bia = User.objects.create_user('bia', 'bia@exemplo.com', 'x')
        perfil_bia = Profile.objects.get(user=bia)

        for perfil in (self.perfil_ana, perfil_bia):
            perfil.telegram_username = ''
            perfil.save()

        self.assertEqual(Profile.objects.filter(telegram_username__isnull=True).count(), 2)

    def test_banco_rejeita_arroba_duplicado(self):
        self.perfil_ana.telegram_username = 'ana_tg'
        self.perfil_ana.save()

        bia = User.objects.create_user('bia', 'bia@exemplo.com', 'x')
        perfil_bia = Profile.objects.get(user=bia)
        perfil_bia.telegram_username = '@ANA_TG'

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                perfil_bia.save()

    def test_normalize_de_valores_vazios(self):
        for valor in ('', '   ', '@', None):
            self.assertIsNone(normalize_telegram_username(valor))


def permissoes_do_grupo(nome):
    """Permissões de um grupo no formato "app_label.codename", como em GROUP_PERMISSIONS"""

    grupo = Group.objects.get(name=nome)

    return {
        '{}.{}'.format(p.content_type.app_label, p.codename)
        for p in grupo.permissions.select_related('content_type')
    }


class DefaultGroupsTests(TestCase):
    """Os três grupos padrão do sistema"""

    def test_os_tres_grupos_existem(self):
        nomes = set(Group.objects.values_list('name', flat=True))

        self.assertTrue({'common_users', 'contributors', 'admins'}.issubset(nomes))

    def test_common_users_pode_solicitar_contribuicao(self):
        grupo = Group.objects.get(name='common_users')
        codenames = set(grupo.permissions.values_list('codename', flat=True))

        self.assertIn('add_solicitation', codenames)
        self.assertIn('view_solicitation', codenames)

    def test_cada_grupo_tem_exatamente_o_que_o_dicionario_declara(self):
        """Num banco novo, o post_migrate deixa cada grupo com o dicionário.

        Pega tanto permissão faltando quanto permissão sobrando: num banco novo
        não há nada concedido à mão, então qualquer sobra veio do código.
        """

        for nome, esperado in GROUP_PERMISSIONS.items():
            with self.subTest(grupo=nome):
                self.assertEqual(permissoes_do_grupo(nome), set(esperado))

    def test_contribuidor_pode_enviar_planta_doenca_e_foto(self):
        codenames = permissoes_do_grupo('contributors')

        self.assertIn('herbarium.add_photo', codenames)
        self.assertIn('disease.add_photodisease', codenames)
        self.assertIn('herbarium.add_plant', codenames)
        self.assertIn('disease.add_disease', codenames)

    def test_contribuidor_nao_aprova_nem_pede_de_novo(self):
        codenames = permissoes_do_grupo('contributors')

        self.assertNotIn('herbarium.approve_photo', codenames)
        self.assertNotIn('disease.approve_photodisease', codenames)
        # Quem já é contribuidor não solicita de novo
        self.assertNotIn('accounts.add_solicitation', codenames)

    def test_administrador_aprova_fotos_dos_dois_herbarios(self):
        codenames = permissoes_do_grupo('admins')

        self.assertIn('herbarium.approve_photo', codenames)
        self.assertIn('disease.approve_photodisease', codenames)

    def test_administrador_tem_tudo_que_o_contribuidor_tem(self):
        self.assertTrue(
            permissoes_do_grupo('contributors').issubset(permissoes_do_grupo('admins'))
        )

    def test_gestao_de_alertas_continua_fora_dos_grupos(self):
        """Decisão registrada em accounts/permissions.py: alerts.* é só superusuário"""

        for nome in DEFAULT_GROUPS:
            with self.subTest(grupo=nome):
                self.assertFalse(
                    any(c.startswith('alerts.') for c in permissoes_do_grupo(nome))
                )


class EnsureDefaultGroupsTests(TestCase):
    """O receiver que sincroniza os grupos com GROUP_PERMISSIONS"""

    def test_e_idempotente(self):
        antes = {nome: permissoes_do_grupo(nome) for nome in DEFAULT_GROUPS}

        ensure_default_groups()
        ensure_default_groups()

        for nome in DEFAULT_GROUPS:
            with self.subTest(grupo=nome):
                self.assertEqual(permissoes_do_grupo(nome), antes[nome])

    def test_preserva_permissao_concedida_por_fora(self):
        """O deploy não pode tirar de um grupo o que foi dado pelo /admin/"""

        extra = Permission.objects.get(
            content_type__app_label='core', codename='change_highlight'
        )
        Group.objects.get(name='admins').permissions.add(extra)

        ensure_default_groups()

        self.assertIn('core.change_highlight', permissoes_do_grupo('admins'))
        self.assertTrue(set(ADMIN_PERMISSIONS).issubset(permissoes_do_grupo('admins')))

    def test_repoe_permissao_removida_por_fora(self):
        grupo = Group.objects.get(name='contributors')
        grupo.permissions.clear()

        ensure_default_groups()

        self.assertEqual(permissoes_do_grupo('contributors'), set(CONTRIBUTOR_PERMISSIONS))
