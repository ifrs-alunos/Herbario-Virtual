# Generated by Django 3.2.7 on 2025-02-05 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp_messages', '0004_alter_messageconfirmation_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageconfirmation',
            name='telegram_chat_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
