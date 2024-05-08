from alerts.models import WhatsappNumber


def whatsapp(_request):
    return {
        "number": WhatsappNumber.objects.first()
    }
