from django.urls import path
from .views import (
    AlertsForDiseasesView,
    SetTelegramWebhookView,
    telegram_webhook,
    verify_whatsapp,
    WhatsAppWebhookView,
    WhatsAppAlertPreferencesView
)

app_name = "whatsapp_messages"

urlpatterns = [
    path("preferences/", WhatsAppAlertPreferencesView.as_view(), name="alert_preferences"),
    path("whatsapp/webhook/", WhatsAppWebhookView.as_view(), name="whatsapp_webhook"),
    path("telegram/webhook/", telegram_webhook, name="telegram_webhook"),
    path("telegram/set_webhook/", SetTelegramWebhookView.as_view(), name="set_telegram_webhook"),
    path("alerts/diseases/", AlertsForDiseasesView.as_view(), name="alerts_for_diseases"),
    path("verify/", verify_whatsapp, name="verify_whatsapp"),
]