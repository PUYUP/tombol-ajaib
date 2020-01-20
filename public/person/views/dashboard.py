from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _


@method_decorator(login_required(login_url='login'), name='dispatch')
class ValidationView(View):
    template_name = 'person/templates/dashboard/validation.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Validasi")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class SecurityView(View):
    template_name = 'person/templates/dashboard/security.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Keamanan")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class DashboardView(View):
    template_name = 'person/templates/dashboard/dashboard.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Dasbor")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class ProfileView(View):
    template_name = 'person/templates/dashboard/profile.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Profil")
        return render(request, self.template_name, self.context)
