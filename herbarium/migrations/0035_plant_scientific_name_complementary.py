# Generated by Django 3.1.3 on 2020-12-14 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0034_auto_20201207_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='plant',
            name='scientific_name_complementary',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='Nome Científico Complementar'),
        ),
    ]
