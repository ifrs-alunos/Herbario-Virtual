from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import localtime, make_aware

from alerts.forms import MathModelForm, ChooseMathModelForm
import plotly.graph_objects as go
from plotly.offline import plot
from datetime import datetime
from django.db.models import Avg

from alerts.models import SensorInMathModel, MathModel

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred") * 2


def verify_require(requirements, value):
	r = [eval(re.replace('x', str(value))) for re in requirements]
	if False in r:
		return False
	else:
		return True


def get_reports(start, end, time_interval, requirements, mathmodel, fig):
	sensors_in_math = SensorInMathModel.objects.filter(mathmodel=mathmodel)
	data = {}
	data_x = []
	data_y = []
	sensors_in_graph = sensors_in_math.filter(in_graph=True).first()
	sensors_in_divider = sensors_in_math.filter(divider=True)

	data_in_graph = {}
	graphs = []

	for sensor_in_math in sensors_in_math:
		if sensor_in_math.mean:
			sensor = sensor_in_math.sensor
			re = requirements.filter(sensor=sensor)
			requires = [x.value_in_relation() for x in re]

			reports = sensor.report_set.filter(time__range=[start, end]).values('time').annotate(avg_value=Avg(
				'value'))

			repo = [x['avg_value'] if verify_require(requires, x['avg_value']) else 0 for x in reports]
			if sensor_in_math.in_graph:
				data_in_graph[sensor.type.name] = repo
			else:
				data[sensor.type.name] = repo
			data_x = [localtime(x['time']) for x in reports]

	exp = mathmodel.source_code
	for key, value in mathmodel.constant_set.all().values_list('name', 'value'):
		exp = exp.replace(key, str(value))

	value = 0
	sig_name = sensors_in_graph.sensor.type.name

	for y, x in enumerate(data_in_graph[sig_name]):
		for d in data:
			if x != 0 and data[d][y] != 0:
				exp_with_mean = exp
				exp_with_mean = exp_with_mean.replace(sig_name, str(x))
				eval_exp = eval(exp_with_mean).real

				value += eval_exp
				data_y.append(value)
			else:
				value = 0
				data_y.append(value)

	fig.add_scatter(x=data_x, y=data_y,
					mode="lines", opacity=0.8,
					line={"color": colors[mathmodel.id]},
					name=mathmodel.name
					)

	for x in sensors_in_divider:
		sensor = x.sensor
		sensor_name = sensor.type.name
		re = requirements.filter(sensor=sensor)
		requires = [x.value_in_relation() for x in re]
		report = sensor.report_set.filter(time__range=[start, end]).values('time').annotate(avg_value=Avg(
			'value')).first()
		if report['avg_value'] == 1:
			time_divider = localtime(report['time'])

			fig.add_vline(x=time_divider.timestamp() * 1000, line_width=3, line_dash="dash", line_color="green",
						  annotation_text=sensor_name, annotation_font_size=20)


def view_graphs(request):
	fig = go.Figure()
	if request.GET.get("date_since") is not None:
		start = datetime.fromisoformat(request.GET.get("date_since"))
		start = make_aware(start, timezone=timezone.utc)
		end = datetime.fromisoformat(request.GET.get("date_until"))
		end = make_aware(end, timezone=timezone.utc)
		for x in request.GET.getlist('mathmodel'):
			mathmodel = MathModel.objects.get(id=x)
			requirements = mathmodel.requirement_set.all()
			get_reports(start, end, 5, requirements, mathmodel, fig)

		plot_element = plot(fig, output_type='div')
	else:
		plot_element = ''

	form_range = MathModelForm()
	form_choose = ChooseMathModelForm()
	context = {'form_range': form_range,
			   'form_choose': form_choose,
			   'plot': plot_element,
			   }

	return render(request, 'view_graphs.html', context)
