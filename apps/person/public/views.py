from django.views import View
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _


class RegisterView(View):
    template_name = 'templates/person/register.html'
    context = dict()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('person'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, self.context)


class RecoveryView(View):
    template_name = 'templates/person/recovery.html'
    context = dict()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('person'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        self.context['title'] = _("Set Ulang Kata Sandi")
        return render(request, self.template_name, self.context)


class LoginView(View):
    template_name = 'templates/person/login.html'
    context = dict()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('person'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        self.context['title'] = _("Masuk")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class ValidationView(View):
    template_name = 'templates/person/validation.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Validasi")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class SecurityView(View):
    template_name = 'templates/person/security.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Keamanan")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class DashboardView(View):
    template_name = 'templates/person/dashboard.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Dasbor")
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class ProfileView(View):
    template_name = 'templates/person/profile.html'
    context = dict()

    def get(self, request):
        self.context['title'] = _("Profil")
        return render(request, self.template_name, self.context)
