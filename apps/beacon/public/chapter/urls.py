from django.urls import path, include

from .views import ChapterRevisionDetailView

urlpatterns = [
    path('<uuid:chapter_uuid>/', ChapterRevisionDetailView.as_view(),
         name='chapter_revision_detail'),
]
