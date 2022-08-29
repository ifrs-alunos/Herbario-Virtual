
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from django.views.generic import CreateView, UpdateView, ListView, DeleteView

from ..forms.sensor_human_form import SensorHumanForm

from alerts.models import MathModel, Sensor


class MathModelListView(ListView):
	model = MathModel
	context_object_name = 'mathmodels'
	template_name = 'dashboard/mathmodel_update.html'
	paginate_by = 12

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'mathmodel-update'  # Cria novo contexto

		return data


class CreateMathModel(CreateView):
	model = MathModel
	template_name = 'dashboard/mathmodel_create_form.html'
	fields = '__all__'
	success_url = reverse_lazy('dashboard:mathmodel_update')


class UpdateMathModel(UpdateView):
	model = MathModel
	template_name = 'dashboard/mathmodel_create_form.html'
	fields = '__all__'
	success_url = reverse_lazy('dashboard:mathmodel_update')


class DeleteMathModel(DeleteView):
	model = MathModel
	template_name = 'dashboard/mathmodel_confirm_delete.html'
	success_url = reverse_lazy('dashboard:mathmodel_update')


class SensorListView(ListView):
	model = Sensor
	context_object_name = 'sensors'
	template_name = 'dashboard/sensor_update.html'
	paginate_by = 12

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'sensor-update'  # Cria novo contexto

		return data


class SensorHumanListView(ListView):
	model = Sensor
	context_object_name = 'sensors'
	template_name = 'dashboard/sensor_human_update.html'
	paginate_by = 12

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'sensor-human-update'  # Cria novo contexto

		return data

	def get_queryset(self):
		qs = Sensor.objects.all().filter(type__metric='bool')
		return qs


def create_sensor_human(request, pk):
	"""Função que cria um novo sensor humano"""

	if request.method == "POST":
		updated_request = request.POST.copy()
		if updated_request['choice']:
			updated_request.update({'value': '1','sensor':pk})
		form = SensorHumanForm(updated_request)

		if form.is_valid():
			form.save()

			return redirect('dashboard:sensor_human_update')

	else:
		form = SensorHumanForm()

	context = {
		'form': form,
	}

	# Renderiza a página de criar sensor
	return render(request, 'dashboard/sensor_human_add.html', context)
