from django.http import JsonResponse
from django.utils.timezone import localtime

from alerts.models import Station


def get_station(request, station_id):
    station = Station.objects.get(id=station_id)
    sensores = station.sensor_set.all()

    dict_station ={
        "station": station_id,
        "station_id":station.station_id,
        "sensors": {}
    }
    for sensor in sensores:
        dict_station["sensors"][sensor.id] = sensor.name

    return JsonResponse(dict_station)
