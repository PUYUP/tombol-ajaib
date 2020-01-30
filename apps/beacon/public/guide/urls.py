from django.urls import path, include

# Guide Views
from .views import (
    GuideListView, GuideRevisionEditorView,
    GuideRevisionDetailView)

urlpatterns = [
    path('', GuideListView.as_view(), name='guide'),
    path('<uuid:guide_uuid>/', GuideRevisionDetailView.as_view(),
         name='guide_revision_detail'),
    path('<uuid:guide_uuid>/change/', GuideRevisionEditorView.as_view(),
         name='guide_revision_editor'),
]
