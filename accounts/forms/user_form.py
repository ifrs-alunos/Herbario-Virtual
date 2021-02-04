from django import forms
from django.forms import widgets

from django.contrib.auth.forms import UserCreationForm

from ..models import User

# from django.contrib.auth.models import User 

# class UserForm(UserCreationForm):

#     class Meta(UserCreationForm.Meta):
#         model = User
#         fields = UserCreationForm.Meta.fields + ('name', 'email',)