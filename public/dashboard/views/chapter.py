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
Chapter = get_model('beacon', 'Chapter')
ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')


@method_decorator(login_required(login_url='login'), name='dispatch')
class ChapterListDashbordView(View):
    template_name = 'dashboard/templates/chapter/list.html'
    context = dict()

    def get(self, request, guide_revision_uuid=None):
        person = request.person
        person_pk = getattr(person, 'pk', None)
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        guide_revision_uuid = check_uuid(uid=guide_revision_uuid)
        if not guide_revision_uuid:
            raise Http404(_("Guide UUID invalid."))

        # ...
        # GuideRevision object
        # ...
        guide_revision_obj = GuideRevision.objects \
            .prefetch_related(
                Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .filter(uuid=guide_revision_uuid, creator_id=person_pk) \
            .annotate(
                num_explain=Count('guide__explains', distinct=True),
                num_chapter=Count('guide__chapters', distinct=True)) \
            .first()

        if not guide_revision_obj:
            raise Http404(_("Tidak ditemukan."))

        self.context['identifier'] = 'chapter'
        self.context['title'] = guide_revision_obj.label
        self.context['guide_revision_uuid'] = guide_revision_uuid
        self.context['guide_revision_obj'] = guide_revision_obj
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
        self.context['status_choices'] = status_choices
        return render(request, self.template_name, self.context)
