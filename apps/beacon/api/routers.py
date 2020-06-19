from django.urls import path, include

# DRF
from rest_framework.routers import DefaultRouter

from .guide.views import GuideApiView
from .guide_revision.views import GuideRevisionApiView
from .introduction.views import IntroductionApiView
from .chapter.views import ChapterApiView
from .chapter_revision.views import ChapterRevisionApiView
from .explain.views import ExplainApiView
from .explain_revision.views import ExplainRevisionApiView
from .sheet.views import SheetApiView
from .topic.views import TopicApiView
from .enrollment.views import EnrollmentGuideApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('guides', GuideApiView, basename='guide')
router.register('guides-revisions', GuideRevisionApiView, basename='guide_revision')
router.register('guides-enrollments', EnrollmentGuideApiView, basename='enrollment_guide')
router.register('introductions', IntroductionApiView, basename='introduction')
router.register('chapters', ChapterApiView, basename='chapter')
router.register('chapters-revisions', ChapterRevisionApiView, basename='chapter_revision')
router.register('explains', ExplainApiView, basename='explain')
router.register('explains-revisions', ExplainRevisionApiView, basename='explain_revision')
router.register('sheets', SheetApiView, basename='sheet')
router.register('topics', TopicApiView, basename='topic')

app_name = 'beacon'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls, 'beacon'), namespace='beacons')),
]
