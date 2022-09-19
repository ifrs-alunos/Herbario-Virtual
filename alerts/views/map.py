from alerts.models import Station
from django.shortcuts import render
from django.utils.timezone import localtime
from django.shortcuts import render
import folium


def get_map(request):
    """Esta função cria um mapa mostrando todas as estações cadastradas
    e suas respectivas situações. Consulte a codumentação do Folium para saber mais sobre poup, icons, tooltips, markers..."""

    query_station = Station.objects.all() # Lista de todas as estações

    m = folium.Map(location=[-28.43, -50.921371], zoom_start=10) # Cria o mapa base
    
    for station in query_station:
            custom_tooltip = ''
            pop_up = ''
            if len(station.sensor_set.all()) == 0: 
                icon_color = 'lightgray'
                custom_tooltip = f"<b>Estação {station.alias}</b><br><br>Sem dados para esta estação no momento." 
                custom_icon = folium.Icon(color=icon_color, icon="fa-circle", prefix='fa',)
                pop_up=folium.Popup(station.description)
            
            else:
                custom_tooltip+= f"<b>Estação {station.alias}</b><br><br>"
                detected = False
                report_exists = 0
                for sensor in station.sensor_set.all():
                    if sensor.report_set.last():
                        report_exists += 1
                        sensor_report = sensor.report_set.last() # Último report do sensor
                        if sensor.type.metric == 'bool': 
                            sensor_value = float(sensor_report.value)
                            if sensor_value == 1.00: # Altera cor e mensagem no mapa caso valor seja 1 (esporos detectados)
                                detected=True
                                custom_tooltip += f"<b>{sensor.name}</b>: DETECTADOS<br>Atualizado: {localtime(sensor_report.time):%d/%m/%Y %H:%M}<br><br>"
                            else: 
                                custom_tooltip += f"<b>{sensor.name}</b>: não detectados<br>Atualizado: {localtime(sensor_report.time):%d/%m/%Y %H:%M}<br><br>"
                        else:    
                            value = float(sensor_report.value)
                            custom_tooltip += f"<b>{sensor.name}</b>: {value:.2f} {sensor.type.metric}<br>Atualizado: {localtime(sensor_report.time):%d/%m/%Y %H:%M}<br><br>"
                if report_exists == 0:
                    custom_tooltip += "Sem dados para esta estação no momento"
                    icon_color = 'lightgray'        
                elif not detected:
                    icon_color = 'green'
                else:
                    icon_color = 'red'
                custom_icon = folium.Icon(color=icon_color, icon="fa-circle", prefix='fa', )
                pop_up = station.description

            folium.Marker([station.lat_coordinate, station.lon_coordinate], tooltip= custom_tooltip, popup= pop_up, icon=custom_icon).add_to(m)

    m = m._repr_html_() # Transforma o mapa em um html pronto para ser renderizado no template

    context = {
        'mapa': m,
    }
    
    return render(request, 'map.html', context)
