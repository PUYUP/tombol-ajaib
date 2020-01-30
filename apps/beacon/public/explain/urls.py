from django.urls import path, include

from .views import (
    ExplainRevisionEditorView, ExplainRevisionDetailView)

urlpatterns = [
    path('<uuid:explain_uuid>/', ExplainRevisionDetailView.as_view(),
         name='explain_revision_detail'),
    path('<uuid:explain_uuid>/change/', ExplainRevisionEditorView.as_view(),
         name='explain_revision_editor'),
]
