from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import PermissionRequiredMixin

# Create your views here.

# class DashboardView(View):
    # def get(self, request, *args, **kwargs):
    #     # Verifica se o usuário na sessão é superuser ou não
    #     if request.user.is_superuser:
    #         view = AdministrativeDashboardView.as_view()
    #     else:
    #         view = ContributorDashboadView.as_view()
        
    #     return view(request, *args, **kwargs)
    
class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"

class ProfileView(TemplateView):
    template_name = "dashboard/profile.html"

# Classe Painel do Administrador
class AdministrativeDashboardView(TemplateView):
    template_name = "dashboard/administrative_dashboard.html"

# Classe Painel do Contribuidor
class ContributorDashboadView(TemplateView):
    template_name = "dashboard/contributor_dashboard.html"

class CreatePlantView(PermissionRequiredMixin, CreateView):
    permission_required = 'herbarium.add_plant'
    pass

class UpdatePlantView(PermissionRequiredMixin, UpdateView):
    permission_required = 'herbarium.change_plant'
    pass

class DeletePlantView(PermissionRequiredMixin, DeleteView):
    permission_required = 'herbarium.delete_plant'
    pass