from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from .functions import *
from .models.message import Message
from accounts.models import Profile
from django.core.exceptions import MultipleObjectsReturned
from datetime import datetime
# Create your views here.

#https://stackoverflow.com/questions/51710145/what-is-csrf-exempt-in-django
@csrf_exempt
def whatsapp_webhook(request):
	if request.method == 'GET':
		VERIFY_TOKEN = '5Mp70BcUsroL9oWi56yxyLZuq8LEQeGO'
		mode = request.GET['hub.mode']
		token = request.GET['hub.verify_token']
		challenge = request.GET['hub.challenge']

		if mode == 'subscribe' and token == VERIFY_TOKEN:
			return HttpResponse(challenge, status=200)
		else:
			return HttpResponse("error", status=403)

	if request.method == 'POST':
		data = json.loads(request.body)
		if 'object' in data and 'entry' in data:
			if data['object'] == 'whatsapp_business_account':
				try:
					for entry in data['entry']:
						testPhoneNumber = entry['changes'][0]['value']['metadata']['display_phone_number']
						phoneId = entry['changes'][0]['value']['metadata']['phone_number_id']
						profileName = entry['changes'][0]['value']['contacts'][0]['profile']['name']
						whatsAppId = entry['changes'][0]['value']['contacts'][0]['wa_id']
						fromId = entry['changes'][0]['value']['messages'][0]['from']
						messageId = entry['changes'][0]['value']['messages'][0]['id']
						timestamp = entry['changes'][0]['value']['messages'][0]['timestamp']
						text = entry['changes'][0]['value']['messages'][0]['text']['body']
						phoneNumber = whatsAppId
												
						if text.lower() == 'labfito':
							numero_semddi = phoneNumber[2:]

							if len(numero_semddi) == 10:
								numero_semddi = numero_semddi[:2] + "9" + numero_semddi[2:]

							try:#se user existir no site
								sender = Profile.objects.get(phone=numero_semddi)
								if sender.get_messages == False:
									sender.can_get_messages()
									message = "Número Cadastrado! Você está apto a receber alertas."
								else:
									message = "Você já está apto a receber alertas."

							except:	
								message = "Não foi possível localizar um usuário cadastrado com este número. Por favor, acesse o link abaixo e cadastre-se.\nhttp://labfito.vacaria.ifrs.edu.br"
							
							sendWhatsappMessage(phoneNumber, message)
							message_object = Message(sender_number = testPhoneNumber, receiver_name = profileName, receiver_number = phoneNumber, timestamp = int(timestamp), message_text = message)
							message_object.save()
				except:
					try:
						"""Checa e armazena na mensagem o seu status"""
						for entry in data['entry']:
							status = entry['changes'][0]['value']['statuses'][0]['status']
							number = entry['changes'][0]['value']['statuses'][0]['recipient_id']
							message_id = entry['changes'][0]['value']['statuses'][0]['id']

							timestamp_status = entry['changes'][0]['value']['statuses'][0]['timestamp']
							data_timestamp = datetime.fromtimestamp(int(timestamp_status))

							if status == "sent":
								ultima_mensagem = Message.objects.filter(receiver_number=number).latest('timestamp')
								ultima_mensagem.status_log+="Status: "+status+" - Data e hora: "+str(data_timestamp)+"\n"
								ultima_mensagem.message_id+=message_id
								
							else:
								ultima_mensagem = Message.objects.filter(message_id=message_id).latest('timestamp')
								ultima_mensagem.status_log+="Status: "+status+" - Data e hora: "+str(data_timestamp)+"\n"
							ultima_mensagem.save()

					except Exception as e:
						print(e)

		return HttpResponse("success", status=200)