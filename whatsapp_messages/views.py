import json
import logging

import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from alerts.forms import AlertsForDiseasesForm
from whatsapp_messages.functions import (
    send_telegram_message,
    set_webhook,
)
from whatsapp_messages.models.message_confirmation import (
    CODE_LENGTH,
    MessageConfirmation,
)

logger = logging.getLogger('django')

@csrf_exempt
def telegram_webhook(request):
    event_data = json.loads(request.body.decode("utf-8"))

    telegram_chat_id = event_data.get('message', {}).get('from', {}).get('id')
    text = event_data.get('message', {}).get('text')

    logger.info(f"Received message from {telegram_chat_id}: {text}")

    if MessageConfirmation.objects.filter(telegram_chat_id=telegram_chat_id).exists():
        send_telegram_message(telegram_chat_id,
                              "Você já vinculou sua conta do Telegram.\n"
                              f"Acesse https://labfito.vacaria.ifrs.edu.br{reverse('whatsapp_messages:link')} "
                              f"para selecionar as doenças que deseja receber alertas.")
        return HttpResponse(status=200)

    try:
        mc = MessageConfirmation.objects.get(code=text)
        mc.verified = True
        mc.telegram_chat_id = telegram_chat_id
        mc.save()
        send_telegram_message(telegram_chat_id, "Sua conta do Telegram foi vinculada com sucesso!\n"
                                                f"Acesse https://labfito.vacaria.ifrs.edu.br{reverse('whatsapp_messages:link')} "
                                                f"para selecionar as doenças que deseja receber alertas.")

    except MessageConfirmation.DoesNotExist:
        send_telegram_message(telegram_chat_id, "Código inválido. Por favor, tente novamente.")

    return HttpResponse(status=200)

class LinkUserTelegramView(TemplateView, LoginRequiredMixin):
    template_name = "whatsapp_messages/link.html"

    def get_context_data(self, **kwargs):
        profile = self.request.user.profile
        try:
            mc = MessageConfirmation.objects.get(profile=profile)
            if mc.has_expired() and not mc.verified:
                mc.delete()
                mc = MessageConfirmation(profile=profile)
                mc.save()
        except MessageConfirmation.DoesNotExist:
            mc = MessageConfirmation(profile=profile)
            mc.save()

        context = super().get_context_data(**kwargs)
        context["message_confirmation"] = mc
        context["bot_telegram_username"] = settings.TELEGRAM_BOT_USERNAME
        context["link"] = "link-telegram"

        form = AlertsForDiseasesForm(profile=profile)
        context["form"] = form

        return context

class SetTelegramWebhookView(View):
    def get(self, request):
        logger.info("Setting webhook via control panel")
        response = set_webhook(request)
        logger.info(response)
        return redirect("whatsapp_messages:link")

class AlertsForDiseasesView(View):
    form_class = AlertsForDiseasesForm

    def post(self, request):
        profile = request.user.profile
        form = self.form_class(request.POST, profile=profile)

        if form.is_valid():
            profile.alerts_for_diseases.set(form.cleaned_data["alerts_for_diseases"])
            profile.save()

        return redirect("whatsapp_messages:link")
