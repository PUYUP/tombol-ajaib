from django.urls import path, include

from public.views.home import HomeView
from public.dashboard import urls as dashboard_urls

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', include(dashboard_urls)),
]
