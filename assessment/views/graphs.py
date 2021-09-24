import datetime

from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objs import Scatter

from assessment.forms import ReportIntervalForm
from assessment.models import Report
from assessment.views.utils import to_datetime

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred")*2

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

def render_graph(request, station_id):
    params = request.GET

    objects = Report.objects.all().filter(station_id=station_id)

    # se os parametros estiverem definidos, filtra a partir deles
    if params:
        datetime_since = to_datetime(params.get("date_since"), params.get("time_since"))
        datetime_until = to_datetime(params.get("date_until"), params.get("time_until"), until=True)
        filtered_objects = objects.filter(board_time__gte=datetime_since, board_time__lte=datetime_until)
    # se não, mostra os relatórios desde 12 horas atrás
    else:
        filtered_objects = objects.filter(board_time__gte=datetime.datetime.now() - datetime.timedelta(hours=12))

    fields = objects.last().get_fields(exclude=["id", "station_id", "board_time"])

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

    context = {
        "plots": plots,
        "form": ReportIntervalForm
    }

    return render(request, "graphs.html", context=context)
