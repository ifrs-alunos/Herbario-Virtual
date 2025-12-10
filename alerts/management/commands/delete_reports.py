from django.core.management.base import BaseCommand

from alerts.models import Station


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        station_cepadi = Station.objects.get(station_id=23)
        maths = station_cepadi.mathmodel_set.all()
        for math in maths:
            math.mathmodelresult_set.all().delete()
        # sensors_name = ["PTemp", "cnr4_T_C_Avg"]
        #
        # for x in sensors_name:
        #     sensor = Sensor.objects.get(type__name=x)
        #     sensor.reading_set.all().delete()
