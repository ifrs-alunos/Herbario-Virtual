from django.urls import path
from .views import (
    AlertsForDiseasesView,
    LinkUserTelegramView,
    SetTelegramWebhookView,
    telegram_webhook,
)

app_name = "whatsapp_messages"

urlpatterns = [
    path("webhook", telegram_webhook, name="webhook"),
    path("set_webhook", SetTelegramWebhookView.as_view(), name="set_webhook"),
    path("link", LinkUserTelegramView.as_view(), name="link"),
    path('alerts_for_diseases', AlertsForDiseasesView.as_view(), name="alerts_for_diseases"),
]
