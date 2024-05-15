import json
from datetime import timedelta

from django import urls
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from alerts.models.whatsapp import VerificationCode, CODE_EXPIRATION_TIME, CODE_LENGTH
from .. import whatsapp


@csrf_exempt
def whatsapp(request):
    if request.method == 'POST':
        # Message is a json object with the following structure:
        # https://docs.wwebjs.dev/Message.html
        data = json.loads(request.body)

        code: str | None = data.get("body")
        if not (isinstance(code, str) and (len(code) == CODE_LENGTH and code.isnumeric())):
            whatsapp.send_message(data.get("from").split("@")[0],
                                  "Código inválido. Por favor, digite um código de 6 dígitos.")
            return JsonResponse({"message": "invalid verification code"}, status=400)

        vc = VerificationCode.objects.filter(code=code,
                                             created_at__gt=timezone.now() - timedelta(minutes=CODE_EXPIRATION_TIME),
                                             verified=False).first()

        if not vc:
            whatsapp.send_message(data.get("from").split("@")[0],
                                  f"O código enviado não existe ou já expirou.\n"
                                  f"Por favor gere outro código em "
                                  f"{request.build_absolute_uri(reverse('dashboard:profile'))}")
            return JsonResponse({"message": "verification code not found"}, status=400)

        vc.verified = True
        vc.save()

    return JsonResponse({"message": "ok"})
