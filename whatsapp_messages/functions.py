import logging

from django.conf import settings
import requests
from django.http import HttpRequest
from django.urls import reverse
from config.settings import TELEGRAM_BOT_TOKEN
logger = logging.getLogger('django')

def set_webhook(request: HttpRequest):
    """Função responsável por definir o webhook"""
    response = requests.post(
        settings.TELEGRAM_API_URL + f"{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
        json={
            "url": request.build_absolute_uri(reverse("whatsapp_messages:webhook")).replace('http://', 'https://'),
            "allowed_updates": ["message"],
            "secret_token": settings.TELEGRAM_SECRET_TOKEN,
        },
    )

    logger.info(f"Body: {response.request.body}")
    logger.info(response)

    return response.json()


def send_telegram_message(chat_id: str, text: str):
    """Função responsável por enviar mensagens pelo Telegram"""

    response = requests.post(
        settings.TELEGRAM_API_URL + f"{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
        },
    )

    logger.info(f"Message sent to {chat_id}: {text}")
    logger.info(response.json())

    return response.json()
