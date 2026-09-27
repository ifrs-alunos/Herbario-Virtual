from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Upper


def assert_no_duplicate_emails(apps, schema_editor):
    """Aborta a migração se algum e-mail estiver em uso por mais de uma conta.

    Decidir qual conta fica com o e-mail é uma decisão de dono do dado, não de
    migração — então aqui só reportamos e paramos.
    """
    User = apps.get_model('auth', 'User')

    duplicados = (
        User.objects.exclude(email='')
        .annotate(chave=Upper('email'))
        .values('chave')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
    )

    if duplicados:
        detalhe = "\n".join(
            "  {} ({} contas)".format(d['chave'], d['total']) for d in duplicados
        )
        raise RuntimeError(
            "Não é possível tornar o e-mail único: há e-mails repetidos.\n"
            "Rode `manage.py find_duplicate_emails` para ver as contas envolvidas e\n"
            "corrija em /admin/auth/user/ antes de migrar de novo.\n" + detalhe
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_default_groups'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(assert_no_duplicate_emails, migrations.RunPython.noop),
        migrations.RunSQL(
            # auth_user é nome fixo: o projeto não usa AUTH_USER_MODEL customizado.
            #
            # UPPER e não LOWER porque é a expressão que o Postgres recebe do
            # __iexact do Django — indexar LOWER deixaria o índice inutilizável
            # para a busca do bot.
            #
            # O índice é parcial (WHERE email <> '') porque auth.User.email é
            # blank=True com default ''. Um índice total rejeitaria o segundo
            # usuário sem e-mail, inclusive um createsuperuser sem e-mail.
            sql=(
                "CREATE UNIQUE INDEX IF NOT EXISTS auth_user_email_upper_uniq "
                "ON auth_user (UPPER(email)) WHERE email <> '';"
            ),
            reverse_sql="DROP INDEX IF EXISTS auth_user_email_upper_uniq;",
        ),
    ]
