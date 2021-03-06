# Generated by Django 3.1.3 on 2021-06-25 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('herbarium', '0038_auto_20210610_2316'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0005_auto_20210610_2316'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantSolicitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Data de envio')),
                ('status', models.CharField(choices=[('sent', 'Em análise'), ('accepted', 'Aceita'), ('denied', 'Negada')], default='sent', max_length=8)),
                ('new_plant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='herbarium.plant', verbose_name='Nova Planta')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plants_solicitations', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Solicitação de planta',
                'verbose_name_plural': 'Solicitações de plantas',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='PhotoSolicitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Data de envio')),
                ('status', models.CharField(choices=[('sent', 'Em análise'), ('accepted', 'Aceita'), ('denied', 'Negada')], default='sent', max_length=8)),
                ('new_photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='herbarium.photo', verbose_name='Nova Foto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photo_solicitations', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Solicitação de foto',
                'verbose_name_plural': 'Solicitações de fotos',
                'ordering': ['id'],
            },
        ),
    ]
