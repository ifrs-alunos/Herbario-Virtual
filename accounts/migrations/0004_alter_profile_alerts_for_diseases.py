# Generated by Django 3.2.7 on 2025-07-26 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0001_initial'),
        ('accounts', '0003_profile_alerts_for_diseases'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='alerts_for_diseases',
            field=models.ManyToManyField(blank=True, to='disease.Disease', verbose_name='alertas para doenças'),
        ),
    ]
