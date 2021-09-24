from django.urls import path

from .views import save_report, board_notify
from .views import render_graph

app_name = 'assessment'

urlpatterns = [
    path('report/post/', save_report, name="save_report"),
    path('board_notify/', board_notify, name="board_notify"),
    path('graph/<int:station_id>', render_graph, name="render_graph")
]




