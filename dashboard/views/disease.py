from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView

from ..models import DiseaseSolicitation, DiseasePhotoSolicitation

from disease.models import Disease
from disease.forms import DiseaseForm, DiseasePhotoForm


def disease_solicitation(request):
	"""Essa função cria uma solicitação para cadastrar uma nova doença"""

	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição
		disease_form = DiseaseForm(request.POST)
		if disease_form.is_valid():
			disease = disease_form.save()  # Cria objeto mas nao salva no banco de dados
			disease.published = False

			disease_solicitation = DiseaseSolicitation(user=request.user, status='sent', new_disease=disease)
			disease_solicitation.save()
			return redirect('dashboard:disease_update')

	# Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
	else:
		# Cria um formulário em branco
		disease_form = DiseaseForm()

	context = {
		'disease_form': disease_form,
		'link': 'disease-solicitation',
	}

	return render(request, 'dashboard/disease_solicitation.html', context)


def disease_update(request, pk):
	"""Essa função cria uma solicitação para cadastrar uma nova doença"""

	disease = get_object_or_404(Disease, id=pk)

	disease_form = DiseaseForm(request.POST or None, instance=disease)
	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição

		if disease_form.is_valid():
			disease = disease_form.save()
			return redirect('dashboard:disease_update')

	context = {
		'disease_form': disease_form,
		'link': 'disease_update',
		}

	return render(request, 'dashboard/disease_solicitation.html', context)


def disease_photo_solicitation(request):
	"""Essa função cria uma solicitação para enviar uma imagem de uma doença"""

	# Se o usuário mandar dados, ou seja, se a requisição for POST
	if request.method == "POST":
		# Cria uma instância com os dados da requisição
		disease_photo_form = DiseasePhotoForm(request.POST, request.FILES)

		if disease_photo_form.is_valid():
			disease_photo = disease_photo_form.save()  # Cria objeto mas nao salva no banco de dados
			disease_photo.published = False

			disease_photo_solicitation = DiseasePhotoSolicitation(user=request.user, status='sent',
																  new_photo=disease_photo)
			disease_photo_solicitation.save()

			return redirect('dashboard:view_dashboard')

	# Se o usuário apenas solicitar para acessar a página, ou seja, se a requisição for GET
	else:
		# Cria um formulário em branco
		disease_photo_form = DiseasePhotoForm()

	context = {
		'disease_photo_form': disease_photo_form,
		'link': 'disease-photo-solicitation',
	}

	return render(request, 'dashboard/disease_photo_solicitation.html', context)


class DiseasePhotoSolicitationListView(ListView):
	model = DiseasePhotoSolicitation
	context_object_name = 'solicitations'
	template_name = 'dashboard/disease_photo_solicitation_list.html'

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'disease-photo-solicitation-list'  # Cria novo contexto

		return data

	def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
		queryset = super().get_queryset()
		queryset = queryset.filter(status=DiseasePhotoSolicitation.Status.SENT)

		return queryset


class DiseaseListView(ListView):
	model = Disease
	context_object_name = 'diseases'
	template_name = 'dashboard/phytopathological_update.html'
	paginate_by = 12

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'disease_update'  # Cria novo contexto

		return data


class DiseaseSolicitationListView(ListView):
	model = DiseaseSolicitation
	context_object_name = 'solicitations'
	template_name = 'dashboard/disease_solicitation_list.html'

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'disease-solicitation-list'  # Cria novo contexto

		return data

	def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
		queryset = super().get_queryset()
		queryset = queryset.filter(status=DiseaseSolicitation.Status.SENT)

		return queryset


class DiseaseSolicitationListView(ListView):
	model = DiseaseSolicitation
	context_object_name = 'solicitations'
	template_name = 'dashboard/disease_solicitation_list.html'

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)

		data['link'] = 'disease-solicitation-list'  # Cria novo contexto

		return data

	def get_queryset(self):  # Filtra as solicitações que estão com o status "enviada"
		queryset = super().get_queryset()
		queryset = queryset.filter(status=DiseaseSolicitation.Status.SENT)

		return queryset


class DiseaseDetailView(DetailView):
	# Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
	model = Disease
	template_name = 'dashboard/disease_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		return context


class DiseaseSolicitationDetailView(DetailView):
	# Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
	model = DiseaseSolicitation
	template_name = 'dashboard/disease_solicitation_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		return context


class DiseasePhotoSolicitationDetailView(DetailView):
	# Mostra detalhes de uma doença em específico. Passa no contexto os dados de UMA doença
	model = DiseasePhotoSolicitation
	template_name = 'dashboard/disease_photo_solicitation_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		return context


class DiseaseSolicitationDeleteView(DeleteView):
	model = DiseaseSolicitation
	success_url = reverse_lazy('dashboard:disease_solicitation_list')


class DiseasePhotoSolicitationDeleteView(DeleteView):
	model = DiseasePhotoSolicitation
	success_url = reverse_lazy('dashboard:disease_photo_solicitation_list')


class DiseaseDeleteView(DeleteView):
	model = Disease
	success_url = reverse_lazy('dashboard:disease_update')



def accept_disease_solicitation(request, pk):
	if request.method == "GET" and request.user.has_perm('disease.change_disease'):
		disease = DiseaseSolicitation.objects.filter(id=pk).first()
		disease.status = "accepted"
		disease.save()

		nd = disease.new_disease

		nd.published_disease = True
		nd.save()

	return redirect("dashboard:disease_solicitation_list")


def accept_disease_photo_solicitation(request, pk):
	if request.method == "GET" and request.user.has_perm('disease.change_disease'):
		photo_disease = DiseasePhotoSolicitation.objects.filter(id=pk).first()
		photo_disease.status = "accepted"
		photo_disease.save()

		np = photo_disease.new_photo

		np.published = True
		np.save()
	return redirect("dashboard:disease_photo_solicitation_list")

