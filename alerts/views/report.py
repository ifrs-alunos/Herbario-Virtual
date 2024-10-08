import json
from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from alerts.models import IntermediaryRequirement, Reading, Station, Report


@method_decorator(csrf_exempt, name="dispatch")
class ReportView(View):
    def post(self, request):
        # POST body looks like this:
        """
        {
          "chipid":185249135999496,
          "time":"2024-01-01T00:00:00",
          "readings": [
            { "sensor_name": "dht_h", "value": 57.5 },
            { "sensor_name": "dht_t", "value": 17.2 },
            { "sensor_name": "rain", "value": 0 }
          ]
        }
        """

        body = json.loads(request.body.decode("utf-8"))

        station = Station.objects.get(station_id=body.get("chipid"))

        report = Report(station=station)
        if body.get("time"):
            report.time = datetime.fromisoformat(body.get("time"))

        report.save()

        sensors = []

        for reading in body.get("readings"):
            sensor = station.sensor_set.get(type__name=reading.get("sensor_name"))
            sensors.append(sensor)

            reading = Reading(
                sensor=sensor, value=float(reading.get("value")), report=report
            )
            if report.time:
                reading.time = None

            reading.save()

        requirements = IntermediaryRequirement.objects.filter(
            requirements__sensor__in=sensors
        ).distinct()

        for requirement in requirements:
            if requirement.validate():
                # Caso os requerimentos sejam válidos, o modelo matemático é calculado usando os valores da estação
                # a função retorna o resultado do modelo matemático, mas não é utilizada, apenas salva no banco de dados
                requirement.math_model.evaluate_by_station(station)

        return JsonResponse({"message": "ok"}, status=200)


class LastReport(View):
    def get(self, request, station_chip_id):
        station = Station.objects.get(station_id=station_chip_id)
        sensor = station.sensor_set.last()
        last_report = sensor.reading_set.order_by("-time").first()

        return JsonResponse(
            {
                "time": last_report.time,
            }
        )
