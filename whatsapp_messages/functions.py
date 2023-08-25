from django.conf import settings
import requests

def sendWhatsappMessage(phoneNumber, message):
	"""Função responsável por enviar mensagem pelo whatsapp"""
	headers = {"Authorization": settings.WHATSAPP_TOKEN}
	payload = {"messaging_product": "whatsapp",
				"recipient_type": "individual",
				"to": phoneNumber,
				"type": "text",
				"text": {"body": message}
				}
	response = requests.post(settings.WHATSAPP_URL, headers=headers, json=payload)
	ans = response.json()
	return ans