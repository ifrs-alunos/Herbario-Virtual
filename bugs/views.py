from django.db.models import Q
from django.shortcuts import render
from .models import *
from django.views.generic import ListView, DetailView
from accounts.models import *


from django.shortcuts import render

def index(request):
    return render(request, 'bugs/index.html')

def detail(request):
    return render(request, 'meuapp/detail.html')

def pagination(request):
    return render(request, 'meuapp/pagination.html')
