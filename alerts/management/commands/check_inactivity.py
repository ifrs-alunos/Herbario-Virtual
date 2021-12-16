from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

import requests

from alerts.models import Report

TELEGRAM_TOKEN = "2072690727:AAGN5G6lkJNq3KlbLLt1KrN33Q8B6AH8FWk"


class Command(BaseCommand):
    help = 'Checks if the number of reports in the last 10 minutes is between 5 and 1'

    def handle(self, *args, **kwargs):
        report_objects = Report.objects.filter(board_time__gte=timezone.now() - timedelta(minutes=10))
        if 5 >= len(report_objects) >= 1:
            data = {
                "chat_id": 995152065,
                "text": f"ei, a estação parou de enviar, dá uma olhada lá, a última atualização foi em {report_objects.first().board_time:%H:%M} "
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=data)
