from django.urls import path, include
from django.contrib.auth import views as auth_views

from .views import (
    RegisterView,
    LoginView,
    ValidationView,
    DashboardView,
    ProfileView,
    SecurityView,
    RecoveryView)

urlpatterns = [
    path('', DashboardView.as_view(), name='person'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('validation/', ValidationView.as_view(), name='validation'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('security/', SecurityView.as_view(), name='security'),
    path('recovery/', RecoveryView.as_view(), name='recovery'),
]
