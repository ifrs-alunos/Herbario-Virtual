from django.urls import path
from .views import (
    LinkUserWhatsappView,
    WhatsappConnectionView,
    WhatsappLogoutView,
    whatsapp_webhook,
)

app_name = "whatsapp_messages"

urlpatterns = [
    path("webhook", whatsapp_webhook, name="webhook"),
    path("connect", WhatsappConnectionView.as_view(), name="connect"),
    path("logout", WhatsappLogoutView.as_view(), name="logout"),
    path("link", LinkUserWhatsappView.as_view(), name="link"),
]
