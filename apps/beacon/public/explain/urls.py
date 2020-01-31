from django.urls import path, include

from .views import (
    ExplainEditorView, ExplainDetailView)

urlpatterns = [
    path('<uuid:explain_uuid>/', ExplainDetailView.as_view(),
         name='explain_detail'),
    path('<uuid:explain_uuid>/change/', ExplainEditorView.as_view(),
         name='explain_editor'),
]
