from django.urls import path

from .views.map import get_map

from .views import board_notify, formula, view_graphs, collect_data_cepadi, get_sensor_data
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
    path('get/sensor/<int:sensor_id>/data', get_sensor_data, name="get_sensor_data"),

]
