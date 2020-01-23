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

        uuid = check_uuid(uid=guide_revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        # ...
        # General GuideRevision object
        # ...
        try:
            guide_revision_obj = GuideRevision.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
                .select_related('creator', 'creator__user', 'guide') \
                .filter(uuid=uuid, creator_id=person_pk) \
                .annotate(
                    num_explain=Count('guide__explains', distinct=True),
                    num_chapter=Count('guide__chapters', distinct=True)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        # ...
        # ChapterRevision annotate field
        # ...
        chapter_params = dict()
        chapter_fields = ('uuid', 'label', 'version', 'status', 'date_created')
        chapter_revisions = ChapterRevision.objects.filter(chapter__pk=OuterRef('pk'))

        for item in chapter_fields:
            chapter_params['chapter_%s' % item] = Case(
                When(num_revision=1, then=Subquery(chapter_revisions.values(item)[:1])),
                default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Upcoming ChapterRevision
        # Get last DRAFT
        # ...
        upcoming_fields = ('uuid', 'label', 'version')
        upcoming_params = dict()
        upcomings = ChapterRevision.objects \
            .filter(chapter__pk=OuterRef('pk')) \
            .order_by('-version')

        for item in upcoming_fields:
            upcoming_params['upcoming_%s' % item] = Case(
                When(num_revision=1, then=Subquery(upcomings.values(item)[:1])),
                default=Subquery(upcomings.filter(status=DRAFT).values(item)[:1])
            )

        # ...
        # Fetch all Chapter based on GuideRevision
        # ...
        chapter_objs = guide_revision_obj.guide.chapters \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .annotate(
                num_revision=Count('chapter_revisions', distinct=True),
                num_explain=Count('explains', distinct=True),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999),
                **chapter_params,
                **upcoming_params) \
            .order_by('sort_stage')

        # ...
        # Pagination
        # ...
        """
        page = request.GET.get('page', 1)
        paginator = Paginator(chapter_objs, 5)

        try:
            chapter_objs = paginator.page(page)
        except PageNotAnInteger:
            chapter_objs = paginator.page(1)
        except EmptyPage:
            chapter_objs = paginator.page(paginator.num_pages)
        """
        self.context['identifier'] = 'chapter'
        self.context['title'] = guide_revision_obj.label
        self.context['guide_revision_uuid'] = guide_revision_uuid
        self.context['guide_revision_obj'] = guide_revision_obj
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
        self.context['status_choices'] = status_choices
        self.context['chapter_objs'] = chapter_objs
        # self.context['paginator'] = paginator
        return render(request, self.template_name, self.context)
