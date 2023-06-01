from django.urls import path

from .views.map import get_map

from .views import board_notify, formula, view_graphs, collect_data_cepadi, get_sensor_data, collect_data_stationif, \
    get_station_sensors_data, download_data_station, get_station, get_mathmodels, get_station_mathmodel_color
from .views import mathmodel
app_name = 'alerts'

urlpatterns = [
    # path('report/post/', save_report, name="save_report"),
    # path('board_notify/', board_notify, name="board_notify"),
    # path('estacoes/', stations.StationIndex.as_view(), name="stations"),
    # path('estacoes/<slug:slug>', stations.StationDetail.as_view(), name="station_detail"),
    # path('', alerts.AlertsView.as_view(), name="alerts"),
    # path('formula/criar/', formula.create_formula, name="create_formula"),
    path('modelo/<int:pk>', mathmodel.MathModelView.as_view(), name="mathmodel"),
    path('mapa', get_map, name='map_url'),
    path('visualizar/graficos', view_graphs, name="view_graphs"),
    path('coletar_dados/cepadi', collect_data_cepadi, name="collect_data_cepadi"),
    path('coletar_dados/estacaoif', collect_data_stationif, name="collect_data_stationif"),
    path('get/sensor/<int:sensor_id>/<str:date_filter>/data', get_sensor_data, name="get_sensor_data"),
    path('get/estacao/<int:station_id>/sensores', get_station_sensors_data, name="get_station_data"),
    path('baixar/dados/estacao/<int:station_id>', download_data_station, name="dowload_data_station"),
    path('get/estacao/<int:station_id>', get_station, name="get_station"),
    path('get/mathmodels/<int:station_id>/<str:date_filter>', get_mathmodels, name="get_mathmodels"),
    path('get/station/<int:station_id>/mathmodel/<int:mathmodel_id>/color', get_station_mathmodel_color, name="get_station_mathmodel_color"),

]
