from django.urls import path, include

# Guide Views
from .views import (
    GuideListView, GuideSortingView, GuideInitialView,
    GuideDetailView)

urlpatterns = [
    path('', GuideListView.as_view(), name='guide'),
    path('initial/', GuideInitialView.as_view(), name='guide_initial'),
    path('<uuid:guide_uuid>/', GuideDetailView.as_view(),
         name='guide_detail'),
    path('<uuid:guide_uuid>/sorting/', GuideSortingView.as_view(),
         name='guide_sorting'),
]
