
from alerts.models import Station, MathModel, Sensor
from django.shortcuts import render

from disease.models import Disease


def get_map(request):
    """Esta função cria um mapa mostrando todas as estações cadastradas
    e suas respectivas situações. Consulte a codumentação do Folium para saber mais sobre poup, icons, tooltips, markers..."""

    query_station = Station.objects.all() # Lista de todas as estações
    list_disease_has_mathmodel = Disease.objects.all().filter(mathmodel__isnull=False).values_list('id',flat=True)
    mathmodels = MathModel.objects.all().filter(disease_id__in=list_disease_has_mathmodel)
    mathmodel_get = ""
    station_modal = ""
    human_sensor = Sensor.objects.all().filter(type__metric="bool")
    if human_sensor:
        human_sensor = human_sensor[0]
    if request.GET:
        if 'station_modal' in request.GET:
            station_modal = int(request.GET["station_modal"])
            station_modal = Station.objects.get(id=station_modal)

        mathmodel_get = int(request.GET["mathmodel"])

    context = {
        'stations': query_station,
        'mathmodels': mathmodels,
        'mathmodel': mathmodel_get,
        'station_modal': station_modal,
        'human_sensor':human_sensor
    }
    
    return render(request, 'map.html', context)
