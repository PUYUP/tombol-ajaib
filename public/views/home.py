from django.views import View
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _


class HomeView(View):
    template = 'templates/home.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Beranda")
        return render(request, self.template, self.context)
