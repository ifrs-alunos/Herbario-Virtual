# Generated by Django 3.1.3 on 2021-01-15 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20201026_1044'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='highlight',
            options={'ordering': ['id'], 'verbose_name': 'Destaque', 'verbose_name_plural': 'Destaques'},
        ),
        migrations.AddField(
            model_name='highlight',
            name='slug',
            field=models.SlugField(null=True, unique=True, verbose_name='Slug'),
        ),
    ]
