from django.core.management.base import BaseCommand

from alerts.models import Station, Sensor


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        station_cepadi = Station.objects.get(station_id=23)
        sensors_name = [
            "PTemp",
            "cnr4_T_C_Avg",
            "AirTC_Avg",
            "RH",
            "T108_C_Avg",
            "Rain_mm_Tot",
        ]

        for x in sensors_name:
            sensor = Sensor.objects.get(name=x)
            sensor.report_set.all().delete()
