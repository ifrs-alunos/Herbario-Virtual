import json
import logging
from datetime import datetime

import requests
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from accounts.models import Profile
from alerts.models import IntermediaryRequirement, Reading, Station, Report

logger = logging.getLogger('django')


@method_decorator(csrf_exempt, name="dispatch")
class ReportView(View):
    def post(self, request):
        body = json.loads(request.body.decode("utf-8"))
        logger.info(f"Received request body: {body}")

        try:
            station = Station.objects.get(station_id=body.get("chipid"))
        except Station.DoesNotExist:
            logger.error(f"Station with chipid {body.get('chipid')} not found.")
            requests.post("https://ntfy.sh/jkt1mDGXFJ8isvnW", data=body)
            return JsonResponse({"message": "station not found"}, status=404)

        report = Report(station=station)
        if body.get("time"):
            report.time = datetime.fromisoformat(body.get("time"))

        report.save()
        logger.info(f"Created report: {report}")

        sensors = []

        for reading in body.get("readings"):
            sensor = station.sensor_set.get(type__name=reading.get("sensor_name"))
            sensors.append(sensor)

            reading = Reading(
                sensor=sensor, value=float(reading.get("value")), report=report
            )
            

            reading.save()
            logger.info(f"Created reading: {reading}")

        requirements = IntermediaryRequirement.objects.filter(
            requirements__sensor__in=sensors
        ).distinct()

        for requirement in requirements:
            if requirement.validate():
                logger.info(f"Requirement {requirement} validated.")
                requirement.math_model.evaluate_by_station(station)
                for profile in Profile.objects.filter(alerts_for_diseases=requirement.math_model.disease):
                    profile.send_alert(requirement.math_model.disease)
                    logger.info(f"Alert sent to profile {profile} for disease {requirement.math_model.disease}")

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
