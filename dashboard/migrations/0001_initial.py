# Generated by Django 3.2.7 on 2024-05-08 20:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('herbarium', '__first__'),
        ('disease', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantSolicitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Data de envio')),
                ('status', models.CharField(choices=[('sent', 'Em análise'), ('accepted', 'Aceita'), ('denied', 'Negada')], default='sent', max_length=8)),
                ('new_photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='herbarium.photo', verbose_name='Nova Foto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photo_solicitations', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Solicitação de foto',
                'verbose_name_plural': 'Solicitações de fotos',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='DiseaseSolicitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Data de envio')),
                ('status', models.CharField(choices=[('sent', 'Em análise'), ('accepted', 'Aceita'), ('denied', 'Negada')], default='sent', max_length=8)),
                ('new_disease', models.ForeignKey(help_text='Dados relacionados à doença', null=True, on_delete=django.db.models.deletion.CASCADE, to='disease.disease', verbose_name='Nova Doença')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='diseases_solicitations', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Solicitação de doença',
                'verbose_name_plural': 'Solicitações de doenças',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='DiseasePhotoSolicitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Data de envio')),
                ('status', models.CharField(choices=[('sent', 'Em análise'), ('accepted', 'Aceita'), ('denied', 'Negada')], default='sent', max_length=8)),
                ('new_photo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='disease.photodisease', verbose_name='Nova Foto')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='disease_photo_solicitations', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Solicitação de foto',
                'verbose_name_plural': 'Solicitações de fotos',
                'ordering': ['id'],
            },
        ),
    ]
