from branca.element import Element, JavascriptLink

from alerts.models import Station, MathModel
from django.shortcuts import render
from django.utils.timezone import localtime
from django.shortcuts import render
import folium
from django.templatetags.static import static

from disease.models import Disease


def get_map(request):
    """Esta função cria um mapa mostrando todas as estações cadastradas
    e suas respectivas situações. Consulte a codumentação do Folium para saber mais sobre poup, icons, tooltips, markers..."""

    query_station = Station.objects.all() # Lista de todas as estações
    list_disease_has_mathmodel = Disease.objects.all().filter(mathmodel__isnull=False).values_list('id',flat=True)
    mathmodels = MathModel.objects.all().filter(disease_id__in=list_disease_has_mathmodel)

    context = {
        'stations': query_station,
        'mathmodels': mathmodels
    }
    
    return render(request, 'map.html', context)
