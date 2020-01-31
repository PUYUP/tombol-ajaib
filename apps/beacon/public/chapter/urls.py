from django.urls import path, include

from .views import ChapterDetailView

urlpatterns = [
    path('<uuid:chapter_uuid>/', ChapterDetailView.as_view(),
         name='chapter_detail'),
]
