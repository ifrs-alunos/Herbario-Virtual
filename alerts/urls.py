from django.urls import path

from .views import save_report, board_notify
from .views import render_graph
from .views import stations

app_name = 'alerts'

urlpatterns = [
    path('report/post/', save_report, name="save_report"),
    path('board_notify/', board_notify, name="board_notify"),
    path('stations/', stations.StationIndex.as_view(), name="stations"),
    path('stations/<str:station_id>', stations.StationDetail.as_view()),
    path('graph/<str:station_id>', render_graph, name="render_graph")
]
