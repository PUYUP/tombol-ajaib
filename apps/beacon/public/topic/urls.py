from django.urls import path, include

# Guide Views
from .views import (
     TopicGuideListView, TopicGuideDetailView)

urlpatterns = [
     path('<uuid:guide_uuid>/topic/', TopicGuideListView.as_view(),
         name='guide_topic_list'),
     path('<uuid:guide_uuid>/topic/<uuid:topic_uuid>/', TopicGuideDetailView.as_view(),
         name='guide_topic_detail'),
]
