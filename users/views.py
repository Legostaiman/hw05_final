from django.views.generic import CreateView

from django.urls import reverse_lazy

from .forms import CreationForm

import datetime as dt


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"


def year(request):
    return {
        'year':dt.datetime.now().year,
    }
