from django.urls import path, include

# Guide Views
from .views import (
    GuideListView, GuideEditorView,
    GuideDetailView)

urlpatterns = [
    path('', GuideListView.as_view(), name='guide'),
    path('<uuid:guide_uuid>/', GuideDetailView.as_view(),
         name='guide_detail'),
    path('<uuid:guide_uuid>/change/', GuideEditorView.as_view(),
         name='guide_editor'),
]
