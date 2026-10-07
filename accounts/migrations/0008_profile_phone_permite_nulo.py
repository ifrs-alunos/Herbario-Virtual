from django.db import migrations


class Migration(migrations.Migration):
    """Alinha a coluna accounts_profile.phone ao modelo, que aceita NULL.

    O modelo declara `phone` com `null=True` desde o 0001_initial, mas o banco de
    produção veio de um histórico de migrações anterior e manteve a coluna como
    NOT NULL. Com isso, criar um perfil sem telefone falhava com NotNullViolation
    — por exemplo, na tela "Dados pessoais" de um usuário que ainda não tinha
    perfil.

    Não dá para resolver com AlterField: para o Django o campo já é nulo, então a
    migração não geraria SQL nenhum. Daí o RunSQL. Num banco criado pelo
    0001_initial a coluna já aceita NULL, e o DROP NOT NULL não faz nada.

    O telefone continua `unique`: vários perfis podem ficar sem telefone porque o
    Postgres não considera dois NULL iguais.
    """

    dependencies = [
        ('accounts', '0007_remove_profile_alert_regions'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "accounts_profile" ALTER COLUMN "phone" DROP NOT NULL;',
            # Sem reverso: voltar a exigir o telefone falharia assim que existisse
            # um perfil sem ele.
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
