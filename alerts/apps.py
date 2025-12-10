import logging
import os
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class AlertsConfig(AppConfig):
    name = 'alerts'
    
    def ready(self):
        import alerts.signals
        print("✅ SIGNALS registrados - processamento por readings")