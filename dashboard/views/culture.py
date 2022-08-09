
from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse_lazy

from django.views.generic import ListView, DeleteView

from ..forms import CultureSolicitationModelForm

from disease.models import Culture



def culture_solicitation(request):
	"""Essa função cria uma solicitação para cadastrar uma nova cultura"""

	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição
		culture_form = CultureSolicitationModelForm(request.POST)

		if culture_form.is_valid():
			culture_form = culture_form.save()  # Cria objeto mas nao salva no banco de dados

			return redirect('dashboard:culture_list')

	# Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
	else:
		# Cria um formulário em branco
		culture_form = CultureSolicitationModelForm()

	context = {
		'culture_form': culture_form,
		'link': 'culture_solicitation',
	}

	return render(request, 'dashboard/culture_solicitation.html', context)


def culture_update(request, pk):
	"""Essa função cria uma solicitação para cadastrar uma nova doença"""

	culture = get_object_or_404(Culture, id=pk)

	culture_form = CultureSolicitationModelForm(request.POST or None, instance=culture)
	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição

		if culture_form.is_valid():
			culture_form.save()

			return redirect('dashboard:culture_list')

	context = {
		'culture_form': culture_form,
		'link': 'culture_update',
	}

	return render(request, 'dashboard/culture_solicitation.html', context)

class CultureDeleteView(DeleteView):
	model = Culture
	success_url = reverse_lazy('dashboard:culture_list')



class CultureListView(ListView):
	model = Culture
	context_object_name = 'culture'
	template_name = 'dashboard/culture_list.html'
	paginate_by = 12

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'culture_list'  # Cria novo contexto

		return data