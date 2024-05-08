import requests
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from alerts.constants import WHATSAPP_API_URL
from alerts.models.whatsapp import WhatsappNumber


class WhatsappBaseMixin(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='admins').exists()


class WhatsappStatusView(WhatsappBaseMixin, TemplateView):
    template_name = "dashboard/whatsapp.html"

    def get(self, request, *args, **kwargs):
        self.extra_context = {"errors": []}

        # Get the status of the WhatsApp API
        try:
            response = requests.get(WHATSAPP_API_URL + '/qr')
        except requests.exceptions.ConnectionError:
            self.extra_context["errors"].append("Falha ao se conectar com o WhatsApp")
            return super().get(request, *args, **kwargs)

        if response.status_code == 200:  # bot is not connected, showing qr code
            qrcode = response.json().get('qrcode')
            if not qrcode:
                self.extra_context["errors"].append("QR Code não encontrado")
            else:
                self.extra_context['qrcode'] = qrcode

            self.extra_context['bot_connected'] = False

            return super().get(request, *args, **kwargs)

        response = requests.get(WHATSAPP_API_URL + '/status')
        """
        response.json() returns:
        {
          "connected": true,
          "info": {
            "pushname": "Bot",
            "wid": {
              "server": "c.us",
              "user": "555400000000",
              "_serialized": "555400000000@c.us"
            },
            "me": {
              "server": "c.us",
              "user": "555400000000",
              "_serialized": "555400000000@c.us"
            },
            "platform": "android"
          }
        }
        """
        if response.status_code != 200:
            self.extra_context["errors"].append("Falha ao obter o status do WhatsApp")
        else:
            self.extra_context['status'] = response.json()

            wa = WhatsappNumber.objects.first()

            # Apenas um número de WhatsApp pode existir
            if not wa:
                WhatsappNumber.objects.create(number=response.json()['info']['me']['user'])
            elif wa.number != response.json()['info']['me']['user']:
                wa.delete()
                WhatsappNumber.objects.create(number=response.json()['info']['me']['user'])

        has_errors = self.extra_context.get('errors')
        self.extra_context['bot_connected'] = not has_errors

        return super().get(request, *args, **kwargs)


class WhatsappLogoutView(WhatsappBaseMixin, View):
    def get(self, request, *args, **kwargs):
        response = requests.get(WHATSAPP_API_URL + '/logout')
        if response.status_code == 200 and response.json().get('success'):
            return redirect('dashboard:whatsapp_status')

        return render(request, 'dashboard/whatsapp.html', {'error': 'Falha ao desconectar o bot'})
