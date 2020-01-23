from django.urls import path, include

from public.dashboard.views.guide import (
    GuideListDashbordView, GuideDetailDashbordView,
    GuideIntroductionDashbordView, GuideInitialDashbordView)
from public.dashboard.views.chapter import ChapterListDashbordView
from public.dashboard.views.explain import ExplainListDashbordView

urlpatterns = [
    path('guide/', GuideListDashbordView.as_view(), name='dashboard_guide_list'),
    path('guide/initial/', GuideInitialDashbordView.as_view(), name='dashboard_guide_initial'),
    path('guide/<uuid:guide_revision_uuid>/', GuideDetailDashbordView.as_view(), name='dashboard_guide_detail'),
    path('guide/<uuid:guide_revision_uuid>/introduction/', GuideIntroductionDashbordView.as_view(), name='dashboard_guide_introduction'),
    path('guide/<uuid:guide_revision_uuid>/chapter/', ChapterListDashbordView.as_view(), name='dashboard_chapter_list'),
    path('guide/<uuid:guide_revision_uuid>/explain/', ExplainListDashbordView.as_view(), name='dashboard_explain_list'),
]
