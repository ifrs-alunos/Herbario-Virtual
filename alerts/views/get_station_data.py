from django.http import JsonResponse
from django.utils.timezone import localtime

from alerts.models import Station


def get_station_data(request, station_id):
    station = Station.objects.get(id=station_id)
    sensores = station.sensor_set.all()
    dict_sensors = {}
    for sensor in sensores:
        if sensor.report_set.last():
            dict_sensors[sensor.id] = {
                "sensor_name": sensor.name,
                "last_report": sensor.report_set.last().value,
                "sensor_metric": sensor.type.metric,
                # "updated": sensor.report_set.last().time.strftime(" %d/%m/%Y %H:%m")
                "updated": localtime(sensor.report_set.last().time).strftime(" %d/%m/%Y %H:%m")

            }

    return JsonResponse(dict_sensors)
