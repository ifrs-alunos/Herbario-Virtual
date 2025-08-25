from django.db.models import Q
from django.shortcuts import render
from .models import *
from django.views.generic import ListView, DetailView
from accounts.models import *

def home(request):
    return render(request, 'bugs/index.html')

def detail(request):
    return render(request, 'bugs/detail.html')

def pagination(request):
    return render(request, 'bugs/pagination.html')
