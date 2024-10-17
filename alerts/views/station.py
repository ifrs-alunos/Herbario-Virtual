from django.http import JsonResponse
from django.utils.timezone import localtime

from alerts.models import Station


def get_station(request, station_id):
    station = Station.objects.get(id=station_id)

    if not station:
        return JsonResponse({"error": "Station not found"}, status=404)

    sensors = station.sensor_set.all()

    dict_station = {
        "station": station_id,
        "station_id": station.station_id,
        "sensors": {},
    }
    for sensor in sensors:
        dict_station["sensors"][sensor.id] = sensor.name

    return JsonResponse(dict_station)


def get_station_sensors_data(request, station_id):
    station = Station.objects.get(id=station_id)

    if not station:
        return JsonResponse({"error": "Station not found"}, status=404)

    sensors = station.sensor_set.all()

    dict_sensors = {}
    for sensor in sensors:
        last_report = sensor.reading_set.last()
        if last_report:
            dict_sensors[sensor.id] = {
                "sensor_name": sensor.name,
                "last_report": last_report.value,
                "sensor_metric": sensor.type.metric,
                "updated": localtime(last_report.time).strftime(
                    "%d/%m/%Y %H:%m"
                ),
            }

    return JsonResponse(dict_sensors)


def get_station_mathmodel_color(request, station_id, mathmodel_id):
    station = Station.objects.get(id=station_id)
    if station:
        return JsonResponse(
            {
                "result": station.mathmodel_set.get(id=mathmodel_id)
                .mathmodelresult_set.last()
                .value
            }
        )

    return JsonResponse({"result": "Station not found"}, status=404)
