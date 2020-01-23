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
    DRAFT, ARCHIVE, PUBLISHED, STATUS_CHOICES)

Category = get_model('beacon', 'Category')
Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')
ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideListDashbordView(View):
    template_name = 'dashboard/templates/guide/list.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        person_pk = request.person_pk
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        # ...
        # Get last ExplainRevision
        # ...
        explain_params = dict()
        explain_fields = ('uuid', 'date_created')
        explain_revisions = ExplainRevision.objects \
            .filter(explain__guide__pk=OuterRef('pk')) \
            .order_by('-date_updated')

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_explain=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Get last ChapterRevision
        # ...
        chapter_params = dict()
        chapter_fields = ('uuid', 'date_created')
        chapter_revisions = ChapterRevision.objects \
            .filter(chapter__guide__pk=OuterRef('pk')) \
            .order_by('-date_updated')

        for item in chapter_fields:
            chapter_params['chapter_%s' % item] = Case(
                When(num_chapter=1, then=Subquery(chapter_revisions.values(item)[:1])),
                default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Get last GuideRevision
        # ...
        revision_fields = ('uuid', 'label', 'version')
        revision_params = dict()
        revisions = GuideRevision.objects.filter(guide__pk=OuterRef('pk'))

        for item in revision_fields:
            revision_params['revision_%s' % item] = Case(
                When(num_revision=1, then=Subquery(revisions.values(item)[:1])),
                default=Subquery(revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Upcoming GuideRevision
        # Get last DRAFT
        # ...
        upcoming_fields = ('uuid', 'label', 'version')
        upcoming_params = dict()
        upcomings = GuideRevision.objects \
            .filter(guide__pk=OuterRef('pk')) \
            .order_by('-version')

        for item in upcoming_fields:
            upcoming_params['upcoming_%s' % item] = Case(
                When(num_revision=1, then=Subquery(upcomings.values(item)[:1])),
                default=Subquery(upcomings.filter(status=DRAFT).values(item)[:1])
            )

        # ...
        # Run query
        # ...
        queryset = Guide.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user')) \
            .select_related('creator', 'creator__user') \
            .filter(creator__pk=person_pk) \
            .annotate(
                num_revision=Count('guide_revisions', distinct=True),
                num_explain=Count('explains', distinct=True),
                num_chapter=Count('chapters', distinct=True),
                **revision_params,
                **upcoming_params,
                **chapter_params,
                **explain_params) \
            .defer('explain_uuid', 'explain_date_created', 'chapter_uuid',
                    'chapter_date_created', 'revision_uuid', 'revision_label', 'revision_version',
                    'upcoming_uuid', 'upcoming_label', 'upcoming_version',
                    'num_revision', 'num_explain', 'num_chapter', 'date_created', 'uuid') \
            .values('explain_uuid', 'explain_date_created', 'chapter_uuid',
                    'chapter_date_created', 'revision_uuid', 'revision_label', 'revision_version',
                    'upcoming_uuid', 'upcoming_label', 'upcoming_version',
                    'num_revision', 'num_explain', 'num_chapter', 'date_created', 'uuid')

        # ...
        # Pagination
        # ...
        page = request.GET.get('page', 1)
        paginator = Paginator(queryset, 2)

        try:
            revision_objs = paginator.page(page)
        except PageNotAnInteger:
            revision_objs = paginator.page(1)
        except EmptyPage:
            revision_objs = paginator.page(paginator.num_pages)

        self.context['title'] = _("Panduan Saya")
        self.context['revision_objs'] = revision_objs
        self.context['status_choice'] = status_choices
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
        self.context['paginator'] = paginator
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideDetailDashbordView(View):
    template_name = 'dashboard/templates/guide/detail.html'
    context = dict()

    def get(self, request, guide_revision_uuid=None):
        person = request.person
        person_pk = getattr(person, 'pk', None)

        uuid = check_uuid(uid=guide_revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

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

        self.context['identifier'] = 'guide'
        self.context['title'] = guide_revision_obj.label
        self.context['guide_revision_uuid'] = guide_revision_uuid
        self.context['guide_revision_obj'] = guide_revision_obj
        self.context['DRAFT'] = DRAFT
        self.context['ARCHIVE'] = ARCHIVE
        self.context['PUBLISHED'] = PUBLISHED
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideIntroductionDashbordView(View):
    template_name = 'dashboard/templates/guide/introduction.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideInitialDashbordView(View):
    template_name = 'dashboard/templates/guide/initial.html'
    context = dict()

    def get(self, request):
        categories_obj = Category.objects.all()

        self.context['title'] = _("Kirim Panduan")
        self.context['categories'] = categories_obj
        return render(request, self.template_name, self.context)
