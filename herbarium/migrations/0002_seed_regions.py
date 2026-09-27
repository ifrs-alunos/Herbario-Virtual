from django.db import migrations

# Region.name é CharField(max_length=20); o nome mais longo aqui tem 12 caracteres.
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def seed_regions(apps, schema_editor):
    Region = apps.get_model('herbarium', 'Region')
    for name in REGIOES:
        Region.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0001_initial'),
    ]

    operations = [
        # Sem reverso: apagar as regiões quebraria Plant.occurrence_regions e
        # Disease.occurrence_regions_disease de quem já tiver escolhido.
        migrations.RunPython(seed_regions, migrations.RunPython.noop),
    ]
