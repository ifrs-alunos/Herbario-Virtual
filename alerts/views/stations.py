from ..models import Station
from django.views.generic import ListView, DetailView
import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objs import Scatter

from alerts.forms import StationAndIntervalForm
from alerts.models import ReportOld
from alerts.views.utils import to_datetime

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred") * 2

verbose_names = {
    "dht_h": "Umidade DHT",
    "dht_t": "Temperatura DHT",
    "dht_hi": "Sensação Térmica DHT",
    "bmp_t": "Temperatura BMP",
    "bmp_p": "Pressão BMP",
    "bmp_a": "Altitude BMP",
    "ldr": "Luz LDR",
    "rain": "Chuva",
    "soil": "Umidade do solo",
    "uv": "Luz ultravioleta"
}


class StationIndex(ListView):
    model = Station
    template_name = 'station_index.html'
    context_object_name = 'stations'

    paginate_by = 12

    def get_queryset(self, **kwargs):
        # Seleciona todas as estações

        stations = Station.objects.all()

        return stations


class StationDetail(DetailView):
    # Mostra detalhes de uma estação específica. Passa no contexto os dados de uma estação
    model = Station
    template_name = 'station_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = StationAndIntervalForm

        report_objects = ReportOld.objects.filter(station__id=self.get_object().id)

        params = self.request.GET
        # se os parametros estiverem definidos, filtra a partir deles
        if params:
            datetime_since = to_datetime(params.get("date_since"), params.get("time_since"))
            datetime_until = to_datetime(params.get("date_until"), params.get("time_until"), until=True)
            filtered_objects = report_objects.filter(board_time__gte=datetime_since, board_time__lte=datetime_until)
        # se não, mostra os relatórios desde 12 horas atrás
        else:
            filtered_objects = report_objects.filter(
                board_time__gte=datetime.datetime.now() - datetime.timedelta(hours=12))

        fields = report_objects.last().get_fields(
            exclude=["id", "station_identificator", "station", "board_time", "bmp_t", "bmp_p", "bmp_a", "uv"])

        plots = []
        x_data = [d - datetime.timedelta(hours=3) for d in filtered_objects.values_list("board_time", flat=True)]

        for index, field in enumerate(fields):
            y_data = [d for d in filtered_objects.values_list(field, flat=True)]

            plot_element = plot([Scatter(x=x_data, y=y_data,
                                         mode="lines", opacity=0.8,
                                         line={"color": colors[index]})],
                                output_type='div'
                                )

            plots.append((plot_element, verbose_names[field]))

        context["plots"] = plots

        return context
