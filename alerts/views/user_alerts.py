from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View

from alerts.forms import UserAlertForm
from alerts.models import UserAlert


class UserAlertPostView(View):
    def post(self, request):
        form = UserAlertForm(request.POST, user=request.user)
        if form.is_valid():
            profile = request.user.profile
            diseases = form.cleaned_data["disease"]
            UserAlert.objects.filter(profile=profile).delete()
            for disease in diseases:
                UserAlert.objects.create(profile=profile, disease=disease)
            return redirect("whatsapp_messages:link")
        return HttpResponse(f"<html>{form.as_p()}</html>", status=400)
