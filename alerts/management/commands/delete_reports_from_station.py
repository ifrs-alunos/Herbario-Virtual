from datetime import datetime

import pytz
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from django.utils import timezone
from django.utils.timezone import make_aware

from alerts.models import Station, Sensor, TypeSensor, Report


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):

        station_cepadi = Station.objects.get(station_id=23)
        sensors_name = ["PTemp", "cnr4_T_C_Avg", "AirTC_Avg", "RH", "T108_C_Avg", "Rain_mm_Tot"]

        for x in sensors_name:
            sensor = Sensor.objects.get(name=x)
            sensor.report_set.all().delete()



