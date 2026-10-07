from django.db import migrations

# Mantido literal: uma data migration não deve seguir constantes do código de
# aplicação, que podem mudar depois sem que a migração possa ser reescrita.
DEFAULT_GROUPS = ["common_users", "contributors", "admins"]


def create_default_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in DEFAULT_GROUPS:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Sem reverso: apagar um Group cascateia auth_user_groups e removeria os
        # vínculos de todos os usuários em silêncio.
        migrations.RunPython(create_default_groups, migrations.RunPython.noop),
    ]
