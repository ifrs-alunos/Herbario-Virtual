from django.db import migrations


def hold_existing_photos(apps, schema_editor):
    """Fixa em False as fotos de doença que hoje não aparecem no site.

    Ao contrário do herbário de plantas, o fitopatológico sempre filtrou por
    `published=True` (ver `Disease.published_photos`): as fotos com
    `published=NULL` são exatamente as que **não** estão visíveis — em geral
    porque ainda esperam a aprovação de um administrador.

    Marcar NULL como False não muda nada no que o público vê; só troca o terceiro
    estado por um booleano que o resto do código sabe interpretar. Marcar como
    True, por outro lado, publicaria material não revisado.

    Compare com herbarium/migrations/0004_publish_existing_photos.py: valores
    opostos, mesma regra — preservar o que cada herbário exibe hoje.
    """

    PhotoDisease = apps.get_model('disease', 'PhotoDisease')

    PhotoDisease.objects.filter(published__isnull=True).update(published=False)


class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0002_alter_photodisease_options'),
    ]

    operations = [
        # Sem reverso: ver o comentário equivalente na migração do herbarium.
        migrations.RunPython(hold_existing_photos, migrations.RunPython.noop),
    ]
