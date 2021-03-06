# Generated by Django 3.0.2 on 2020-10-05 13:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0027_plant_occorrence_regions'),
    ]

    operations = [
        migrations.AddField(
            model_name='plant',
            name='importance',
            field=models.TextField(null=True, verbose_name='Importância'),
        ),
        migrations.AlterField(
            model_name='state',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='states', to='herbarium.Region', verbose_name='Região'),
        ),
    ]
