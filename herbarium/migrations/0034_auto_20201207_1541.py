# Generated by Django 3.1.3 on 2020-12-07 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0033_auto_20201207_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True, verbose_name='Identificador'),
        ),
    ]
