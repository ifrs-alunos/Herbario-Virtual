# Auto-generated migration to add condition_text_disease safely
from django.db import migrations, models

def set_empty_condition_text(apps, schema_editor):
    Disease = apps.get_model('disease', 'Disease')
    Disease.objects.filter(condition_text_disease__isnull=True).update(condition_text_disease='')

class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0002_alter_disease_occurrence_regions_disease'),
    ]

    operations = [
        migrations.AddField(
            model_name='disease',
            name='condition_text_disease',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(set_empty_condition_text, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='disease',
            name='condition_text_disease',
            field=models.TextField(blank=True),
        ),
    ]
