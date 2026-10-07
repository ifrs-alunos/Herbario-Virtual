from django.db import migrations


# Nomes iguais aos que o 0001_initial cria, para que esta migração não faça nada
# num banco que já está certo.
FK_NAME = "accounts_contribuiti_profile_id_a62cc3ff_fk_accounts_"
INDEX_NAME = "accounts_contribuition_profile_id_a62cc3ff"

SQL = f"""
ALTER TABLE "accounts_contribuition" ADD COLUMN IF NOT EXISTS "profile_id" integer NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{FK_NAME}') THEN
        ALTER TABLE "accounts_contribuition"
            ADD CONSTRAINT "{FK_NAME}" FOREIGN KEY ("profile_id")
            REFERENCES "accounts_profile" ("id") DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS "{INDEX_NAME}" ON "accounts_contribuition" ("profile_id");
"""


class Migration(migrations.Migration):
    """Cria em accounts_contribuition a coluna profile_id, que o modelo já declara.

    O banco de produção veio de um histórico de migrações anterior ao 0001_initial
    atual e ficou com a tabela só com a coluna `id`. A lista de contribuições do
    painel filtra por `profile` e falhava. A tabela estava vazia em produção
    (verificado em 07/10/2026), então o NOT NULL não tem linha antiga para barrar.

    RunSQL, e não AddField, porque para o Django a coluna já existe desde o
    0001_initial. Tudo aqui é idempotente.
    """

    dependencies = [
        ('accounts', '0008_profile_phone_permite_nulo'),
    ]

    operations = [
        # Sem reverso: num banco criado pelo 0001_initial a coluna é do modelo, e
        # apagá-la quebraria a tabela.
        migrations.RunSQL(sql=SQL, reverse_sql=migrations.RunSQL.noop),
    ]
