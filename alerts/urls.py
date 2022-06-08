from django.urls import path

from .views import save_report, board_notify, formula
from .views import stations
from .views import alerts, mathmodel

app_name = 'alerts'

urlpatterns = [
    path('report/post/', save_report, name="save_report"),
    path('board_notify/', board_notify, name="board_notify"),
    path('estacoes/', stations.StationIndex.as_view(), name="stations"),
    path('estacoes/<slug:slug>', stations.StationDetail.as_view(), name="station_detail"),
    path('', alerts.AlertsView.as_view(), name="alerts"),
    path('formula/criar/', formula.create_formula, name="create_formula"),
    path('modelo/<int:pk>', mathmodel.MathModelView.as_view(), name="mathmodel"),
]
