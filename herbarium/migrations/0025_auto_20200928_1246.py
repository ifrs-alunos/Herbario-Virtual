# Generated by Django 3.0.2 on 2020-09-28 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0024_auto_20200928_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='occorrence_states',
            field=models.ManyToManyField(to='herbarium.State', verbose_name='Estados de Ocorrência'),
        ),
    ]
