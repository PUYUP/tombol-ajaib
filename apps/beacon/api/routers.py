from django.urls import path, include

# DRF
from rest_framework.routers import DefaultRouter

from .guide.views import GuideApiView
from .guide_revision.views import GuideRevisionApiView
from .introduction.views import IntroductionApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('guides', GuideApiView, basename='guide')
router.register('guides-revisions', GuideRevisionApiView, basename='guide_revision')
router.register('introductions', IntroductionApiView, basename='introduction')

app_name = 'beacon'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls, 'beacon'), namespace='beacons')),
]
