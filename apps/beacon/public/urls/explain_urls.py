from django.urls import path, include

from ..views.explain import (
    ExplainRevisionEditorView, ExplainRevisionDetailView)

urlpatterns = [
    path('<uuid:revision_uuid>/', ExplainRevisionDetailView.as_view(),
         name='explain_revision_detail'),
    path('<uuid:revision_uuid>/change/', ExplainRevisionEditorView.as_view(),
         name='explain_revision_editor'),
]
