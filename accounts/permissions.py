"""Grupos padrão do sistema e as permissões de cada um.

Este dicionário é a **fonte da verdade** sobre o que cada grupo pode fazer: o
receiver abaixo sincroniza os grupos com ele a cada `post_migrate`, o que
significa que uma permissão concedida à mão pelo `/admin/` a um destes três
grupos será desfeita na próxima migração. Para conceder algo pontual a uma
pessoa, use as permissões individuais do usuário — não mexa nos grupos.

As permissões são atribuídas em `post_migrate` — e não numa data migration — porque
as linhas de `auth.Permission` só são criadas pelo receiver `create_permissions` do
`django.contrib.auth`, que também roda em `post_migrate`. Numa base nova, uma
migração que procurasse por `Permission` não encontraria nada e falharia (ou, pior,
não atribuiria nada em silêncio).
"""

# Grupo dos usuários comuns, atribuído a todo mundo que se cadastra.
COMMON_USERS = "common_users"
# Quem teve a solicitação de contribuidor aceita.
CONTRIBUTORS = "contributors"
# Administradores do sistema.
ADMINS = "admins"

DEFAULT_GROUPS = [COMMON_USERS, CONTRIBUTORS, ADMINS]


# Permissões que definem o contribuidor: enviar planta, doença e foto. As fotos
# nascem despublicadas e dependem de aprovação — ver as views de solicitação em
# dashboard/views/.
CONTRIBUTOR_PERMISSIONS = [
    # Acompanhar a própria solicitação já aceita.
    "accounts.view_solicitation",

    "herbarium.contribute_with_plants",
    "herbarium.add_plant",
    "herbarium.add_photo",

    "disease.contribute_with_disease",
    "disease.add_disease",
    "disease.add_photodisease",

    # Enviar imagem ao bot do Telegram. Permissão própria em vez de reaproveitar
    # herbarium.add_photo: o bot grava TelegramPhoto, que não é foto de planta
    # nenhuma, e ler `herbarium.add_photo` dentro de telegram_bot/ confundiria.
    "telegram_bot.add_telegramphoto",
]

# O administrador é um contribuidor que também revisa: edita, apaga e aprova.
ADMIN_PERMISSIONS = CONTRIBUTOR_PERMISSIONS + [
    "herbarium.change_plant",
    "herbarium.delete_plant",
    "herbarium.change_photo",
    "herbarium.delete_photo",
    "herbarium.approve_photo",

    "disease.change_disease",
    "disease.delete_disease",
    "disease.change_photodisease",
    "disease.delete_photodisease",
    "disease.approve_photodisease",

    # Culturas são o "pai" das doenças no acervo, e o administrador já as gerencia
    # pela tela de culturas do painel. As views passaram a exigir estas permissões
    # em 24/09/2026 (antes eram abertas a qualquer visitante) — sem concedê-las
    # aqui, a gestão de culturas ficaria só para superusuário. Ver as views em
    # dashboard/views/culture.py.
    "disease.add_culture",
    "disease.change_culture",
    "disease.delete_culture",
    "disease.view_culture",

    # Publicações do site, gerenciadas no painel. Mesmo motivo das culturas: as
    # views passaram a exigir permissão em 24/09/2026. Ver dashboard/views/core.py.
    "core.add_publication",
    "core.change_publication",
    "core.delete_publication",
    "core.view_publication",

    # Revisar quem pede para virar contribuidor. `auth.view_user` é o que
    # SolicitationListView/SolicitationUpdateView exigem hoje.
    "accounts.change_solicitation",
    "auth.view_user",
]

# Permissões por grupo, no formato "app_label.codename".
#
# Fora daqui de propósito: a gestão do sistema de alertas (alerts.*) continua
# restrita a superusuário. Abrir isso ao grupo `admins` é uma decisão à parte.
GROUP_PERMISSIONS = {
    # Sem estas duas, o fluxo "pedir para virar contribuidor" é 403 para todo
    # usuário recém-cadastrado: SolicitationCreateView exige accounts.add_solicitation.
    COMMON_USERS: [
        "accounts.add_solicitation",
        "accounts.view_solicitation",
    ],
    # Note que `add_solicitation` não está aqui: quem já é contribuidor não pede
    # de novo, e SolicitationUpdateView tira o usuário de common_users ao promovê-lo.
    CONTRIBUTORS: CONTRIBUTOR_PERMISSIONS,
    ADMINS: ADMIN_PERMISSIONS,
}


def ensure_default_groups(sender=None, **kwargs):
    """Cria os grupos padrão e sincroniza suas permissões. Idempotente.

    Conectado a `post_migrate` sem `sender` (ver accounts/apps.py), então roda uma
    vez por app instalado. É de propósito: as permissões de `herbarium` e `disease`
    só passam a existir no `post_migrate` desses apps, que vem depois do de
    `accounts`. Rodando em todas as passadas, a última encontra tudo criado.
    """

    from django.contrib.auth.models import Group, Permission

    # Uma consulta só para todas as permissões citadas no dicionário — o receiver
    # roda muitas vezes por `migrate` e não vale fazer dezenas de SELECTs em cada.
    desejadas = {entry for entries in GROUP_PERMISSIONS.values() for entry in entries}
    codenames = {entry.split(".")[1] for entry in desejadas}

    existentes = {
        "{}.{}".format(p.content_type.app_label, p.codename): p
        for p in Permission.objects.select_related("content_type").filter(
            codename__in=codenames
        )
    }

    for name in DEFAULT_GROUPS:
        group, _ = Group.objects.get_or_create(name=name)

        entries = GROUP_PERMISSIONS.get(name, [])

        if not entries:
            group.permissions.clear()
            continue

        try:
            permissions = [existentes[entry] for entry in entries]
        except KeyError:
            # App ainda não migrado nesta passada. Sair sem tocar no grupo: um
            # set() com a lista incompleta apagaria o que já estava correto.
            continue

        group.permissions.set(permissions)
