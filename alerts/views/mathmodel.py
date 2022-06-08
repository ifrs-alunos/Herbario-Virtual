from django.views.generic import DetailView
from alerts.models import MathModel, Report
from alerts.views.utils import to_datetime
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import localtime, make_aware
from alerts.forms import MathModelForm
from django.db.models import Avg
from plotly.offline import plot
from plotly.graph_objs import Scatter

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred") * 2


# Função que pega todos os reports do sensor no range por time_interval

def get_reports_requirement_sensor_per_time_interval(report, start, end, time_interval, sensors_type, requirements):
	reports = report.objects.all().filter(time__range=[start, end]).filter(
		sensor__id__in=sensors_type).values()

	first_report = localtime(reports[0]['time']).replace(minute=0, second=0, microsecond=0)
	last_report = (localtime(reports[len(reports) - 1]['time']).replace(minute=59, second=59, microsecond=0))
	report_range = range(0, ((last_report - first_report).days * 1440), time_interval)
	report_time_interval = [(first_report + timezone.timedelta(minutes=x)).replace(second=0, microsecond=0)
							for x in report_range]
	sensors_reports = {}
	for time_int in report_time_interval:
		sensors_reports[time_int] = {}
		for x in sensors_type:
			media = reports.filter(sensor__id=x).filter(time__range=[time_int, time_int + timezone.timedelta(
				minutes=time_interval - 1, seconds=59)]).aggregate(Avg('value'))
			sensors_reports[time_int].update({x: media['value__avg']})
		sensors = sensors_reports[time_int]

		if not check_requires(sensors, requirements):
			sensors_reports[time_int] = {}

	return sensors_reports


def check_requires(dict_sensor, requirements):
	conditions = []
	for x in dict_sensor:
		report_in = dict_sensor[x]
		re = requirements.filter(sensor__id=x)
		requires = [x.value_in_relation() for x in re]
		for require in requires:
			r = require.replace('x', str(report_in))
			re = eval(r)
			if re:
				conditions.append(True)
			else:
				conditions.append(False)
	if False in conditions:
		return False
	else:
		return True


def set_reports_data_to_graph(reports, exp):
	x_data = []
	y_data = []
	reports_in_time_split = []
	sum_t = 0
	for x in reports:
		if reports[x]:
			for y in reports[x]:

				if y == 5:
					mtemp = reports[x][y]
					exp_with_mean = exp
					exp_with_mean = exp_with_mean.replace('graus', str(mtemp))
					eval_exp = eval(exp_with_mean)
					sum_t += eval_exp
					y_data.append(sum_t)
					x_data.append(x)
		else:
			sum_t = 0
			y_data.append(sum_t)
			x_data.append(x)

	return [x_data, y_data]


class MathModelView(DetailView):
	model = MathModel
	template_name = 'mathmodel.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["form"] = MathModelForm

		params = self.request.GET
		# se os parametros estiverem definidos, filtra a partir deles
		mathmodel = self.object
		requirements = mathmodel.requirement_set.all()
		sensors_type = list(set([x.sensor.id for x in requirements]))
		if params:
			start = datetime.fromisoformat(params.get("date_since"))
			start = make_aware(start,timezone=timezone.utc)
			end = datetime.fromisoformat(params.get("date_until"))
			end = make_aware(end,timezone=timezone.utc)

			get_rp = get_reports_requirement_sensor_per_time_interval(Report, start, end, 5, sensors_type, requirements)

			exp = mathmodel.source_code
			for key, value in mathmodel.disease.constant_set.all().values_list('name', 'value'):
				exp = exp.replace(key, str(value))

			data_in_graph = set_reports_data_to_graph(get_rp, exp)
		# se não, mostra os relatórios desde 12 horas atrás
		else:
			start = timezone.datetime(2022, 2, 1, 3, 0, 0, tzinfo=timezone.utc)
			end = timezone.datetime(2022, 3, 1, 2, 59, 59, tzinfo=timezone.utc)
			get_rp = get_reports_requirement_sensor_per_time_interval(Report, start, end, 5, sensors_type, requirements)
			exp = mathmodel.source_code
			for key, value in mathmodel.disease.constant_set.all().values_list('name', 'value'):
				exp = exp.replace(key, str(value))

			data_in_graph = set_reports_data_to_graph(get_rp, exp)
		plot_element = plot([Scatter(x=data_in_graph[0], y=data_in_graph[1],
									 mode="lines", opacity=0.8,
									 line={"color": colors[0]})],
							output_type='div'
							)

		context["plot"] = plot_element

		return context
