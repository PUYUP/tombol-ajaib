from django.views import View
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, Prefetch, Q, F)
from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')
ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')


@method_decorator(login_required(login_url='login'), name='dispatch')
class ExplainListDashbordView(View):
    template_name = 'dashboard/templates/explain/list.html'
    context = dict()

    def get(self, request, guide_revision_uuid=None):
        guide_revision_uuid = check_uuid(uid=guide_revision_uuid)
        if not guide_revision_uuid:
            raise Http404(_("Tidak ditemukan."))

        self.context['identifier'] = 'explain'
        self.context['guide_revision_uuid'] = guide_revision_uuid
        return render(request, self.template_name, self.context)
