# Generated by Django 3.2.7 on 2024-11-05 20:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp_messages', '0002_messageconfirmation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='messageconfirmation',
            old_name='user',
            new_name='profile',
        ),
    ]