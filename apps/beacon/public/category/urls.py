from django.urls import path, include

from .views import CategoryGuideListView

urlpatterns = [
    path('<uuid:category_uuid>/', CategoryGuideListView.as_view(),
         name='category_guide_list'),
]
