from django.urls import path, include

from public.views.home import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]
