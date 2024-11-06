from django.conf import settings
import requests
from django.http import HttpRequest
from django.urls import reverse

from whatsapp_messages.types import WhatsappStatus


def start_whatsapp_session():
    """Função responsável por iniciar a sessão do WhatsApp"""
    headers = {"token": settings.WHATSAPP_TOKEN}
    data = {
        "Subscribe": [
            "Message",
        ],
    }
    response = requests.post(
        settings.WHATSAPP_API_URL + "/session/connect", headers=headers, json=data
    )
    body = response.json()
    return body


def get_whatsapp_qr_code() -> bytes:
    """Função responsável por retornar o QR Code para autenticação"""
    headers = {"token": settings.WHATSAPP_TOKEN}
    response = requests.get(settings.WHATSAPP_API_URL + "/session/qr", headers=headers)
    qrcode = response.json().get("data", {}).get("QRCode")
    return qrcode


def get_whatsapp_status() -> WhatsappStatus:
    """Função responsável por retornar o status do WhatsApp"""
    headers = {"token": settings.WHATSAPP_TOKEN}
    response = requests.get(
        settings.WHATSAPP_API_URL + "/session/status", headers=headers
    )

    if response.status_code != 200:
        return WhatsappStatus(Connected=False, LoggedIn=False)

    return WhatsappStatus(**response.json()["data"])


def set_webhook(request: HttpRequest):
    """Função responsável por definir o webhook"""
    headers = {"token": settings.WHATSAPP_TOKEN}
    response = requests.post(
        settings.WHATSAPP_API_URL + "/webhook",
        headers=headers,
        json={
            "WebhookURL": request.build_absolute_uri(
                reverse("whatsapp_messages:webhook")
            )
        },
    )
    return response.json()


def convert_phone_number(phone_number: str) -> str:
    """
    Converte um número de telefone para o formato necessário pela API.
    Args:
        phone_number: Número de telefone do WhatsApp

    Returns:
        O número de telefone no formato necessário pela API
    """

    return f"55{phone_number[0:2]}{phone_number[3:]}"


def send_whatsapp_message(phone: str, body: str):
    """Função responsável por enviar mensagens pelo WhatsApp"""
    headers = {"token": settings.WHATSAPP_TOKEN}
    data = {
        "Phone": phone,
        "Body": body,
    }
    response = requests.post(
        settings.WHATSAPP_API_URL + "/chat/send/text", headers=headers, json=data
    )

    return response.json()
