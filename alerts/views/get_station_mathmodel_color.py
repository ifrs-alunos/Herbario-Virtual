from django.http import JsonResponse
from django.utils.timezone import localtime

from alerts.models import Station


def get_station_mathmodel_color(request, station_id, mathmodel_id):
    station = Station.objects.get(id=station_id)
    if station:
        return JsonResponse({"result": station.mathmodel_set.get(id=mathmodel_id).mathmodelresult_set.last().value})
