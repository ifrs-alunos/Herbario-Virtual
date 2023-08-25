from django.urls import path
from . import views

app_name = 'whatsapp_messages'

urlpatterns = [
	path('whatsapp-webhook-g4VuZcaqbGP83r340Cpr', views.whatsapp_webhook, name='whatsapp-webhook'),	
]