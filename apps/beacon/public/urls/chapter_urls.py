from django.urls import path, include

from ..views.chapter import ChapterRevisionDetailView

urlpatterns = [
    path('<uuid:revision_uuid>/', ChapterRevisionDetailView.as_view(),
         name='chapter_revision_detail'),
]
