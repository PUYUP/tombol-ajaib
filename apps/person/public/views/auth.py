from django.views import View
from django.shortcuts import render, redirect, reverse
from django.utils.translation import ugettext_lazy as _


class RegisterView(View):
    template_name = 'templates/person/auth/register.html'
    context = dict()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('person'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, self.context)


class RecoveryView(View):
    template_name = 'templates/person/auth/recovery.html'
    context = dict()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('person'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        self.context['title'] = _("Set Ulang Kata Sandi")
        return render(request, self.template_name, self.context)


class LoginView(View):
    template_name = 'templates/person/auth/login.html'
    context = dict()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('person'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        self.context['title'] = _("Masuk")
        return render(request, self.template_name, self.context)
