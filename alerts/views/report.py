import json

import requests
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from alerts.models import Report, Station


@method_decorator(csrf_exempt, name="dispatch")
class ReportView(View):
    def post(self, request):
        # POST body looks like this:
        """
        {
          "chipid":185249135999496,
          "readings": [
            { "sensor_name": "dht_h", "value": 57.5 },
            { "sensor_name": "dht_t", "value": 17.2 },
            { "sensor_name": "rain", "value": 0 }
          ]
        }
        """

        body = json.loads(request.body.decode("utf-8"))

        try:
            station = Station.objects.get(station_id=body.get("chipid"))
        except Station.DoesNotExist:
            requests.post("https://ntfy.sh/jkt1mDGXFJ8isvnW", data=body)
            return JsonResponse({"message": "station not found"}, status=404)

        for reading in body.get("readings"):
            sensor = station.sensor_set.get(type__name=reading.get("sensor_name"))
            Report.objects.create(sensor=sensor, value=float(reading.get("value")))

        #        for sensor in Sensor.objects.filter(used_internally=True):
        #            for requirement in sensor.requirement_set.all():
        #                requirement.validate()

        return JsonResponse({"message": "ok"})


class LastReport(View):
    def get(self, request, station_chip_id):
        station = Station.objects.get(station_id=station_chip_id)
        sensor = station.sensor_set.last()
        last_report = sensor.report_set.order_by("-time").first()

        return JsonResponse(
            {
                "time": last_report.time,
            }
        )
