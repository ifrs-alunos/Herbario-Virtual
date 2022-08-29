from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse_lazy

from django.views.generic import CreateView, ListView, DeleteView
from ..forms import  PublicationForm, PublicationPhotoForm

from core.models import Publication



class PublicationListView(ListView):
	model = Publication
	context_object_name = 'publications'
	template_name = 'dashboard/publication_update.html'
	paginate_by = 12

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'publication_update'  # Cria novo contexto

		return data


def publication_update(request, pk):
	"""Essa função cria uma solicitação para cadastrar uma nova publicação"""

	publication = get_object_or_404(Publication, id=pk)

	publication_form = PublicationForm(request.POST or None, instance=publication)
	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição

		if publication_form.is_valid():
			publication_form.save()

			return redirect('dashboard:publication_update')

	context = {
		'publication_form': publication_form,
		'link': 'publication_update',
	}

	return render(request, 'dashboard/publication_add.html', context)


class PublicationCreateView(CreateView):
	model = Publication
	fields = ['title', 'content']
	template_name = "dashboard/publication_add.html"
	success_url = reverse_lazy('dashboard:publication_update')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['publication_form'] = context["form"]
		return context


class PublicationDeleteView(DeleteView):
	model = Publication
	success_url = reverse_lazy('dashboard:publication_update')


def publication_photo_solicitation(request):
	"""Essa função cria uma imagem de uma publicação"""

	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição
		publication_photo_form = PublicationPhotoForm(request.POST, request.FILES)

		if publication_photo_form.is_valid():
			publication_photo_form.save()  # Cria objeto e salva no banco de dados

			return redirect('dashboard:publication_update')

	# Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
	else:
		# Cria um formulário em branco
		publication_photo_form = PublicationPhotoForm()

	context = {
		'publication_photo_form': publication_photo_form,
		'link': 'publication-photo-solicitation',
	}

	return render(request, 'dashboard/publication_photo_add.html', context)
