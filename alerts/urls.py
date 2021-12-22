from django.urls import path

from .views import save_report, board_notify
from .views import stations

app_name = 'alerts'

urlpatterns = [
    path('report/post/', save_report, name="save_report"),
    path('board_notify/', board_notify, name="board_notify"),
    path('estacoes/', stations.StationIndex.as_view(), name="stations"),
    path('estacoes/<slug:slug>', stations.StationDetail.as_view(), name="station_detail"),
]
