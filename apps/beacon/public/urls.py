from django.urls import path, include

from .views.guide import (
    GuideListView, GuideEditorView, GuideRevisionEditorView,
    GuideRevisionDetailView)

urlpatterns = [
    path('', GuideListView.as_view(), name='guide'),
    path('initial/', GuideEditorView.as_view(), name='guide_initial'),
    path('<uuid:revision_uuid>/', GuideRevisionDetailView.as_view(),
         name='guide_revision_detail'),
    path('<uuid:revision_uuid>/change/', GuideRevisionEditorView.as_view(),
         name='guide_revision_editor'),
]
