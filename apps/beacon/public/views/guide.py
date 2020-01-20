from django.views import View
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, F, Prefetch,
    CharField, IntegerField, Value, Q, Sum)
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Category = get_model('beacon', 'Category')
Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')
Introduction = get_model('beacon', 'Introduction')
ChapterRevision = get_model('beacon', 'ChapterRevision')
Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')


class GuideListView(View):
    """ This case we show last revision based on Guide
    Use last published revision if more than one """
    template_name = 'templates/guide/list.html'
    context = dict()

    def get(self, request):
        revision_fields = ('uuid', 'label', 'date_updated', 'version', 'status')
        revision_params = dict()
        person = request.person
        revisions = GuideRevision.objects.filter(guide__pk=OuterRef('pk'))

        for item in revision_fields:
            revision_params['revision_%s' % item] = Case(
                When(num_revision=1, then=Subquery(revisions.values(item)[:1])),
                default=Subquery(revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        guides = Guide.objects \
            .filter(creator=person) \
            .annotate(
                num_revision=Count('guide_revisions'),
                **revision_params)

        self.context['title'] = _("Panduan Saya")
        self.context['guides'] = guides
        self.context['STATUS_CHOICES'] = STATUS_CHOICES
        return render(request, self.template_name, self.context)


class GuideRevisionDetailView(View):
    template_name = 'templates/guide/detail.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        person = request.person
        person_pk = getattr(person, 'pk', None)
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        # Fields want to display in annotate Chapter
        chapter_params = dict()
        chapter_fields = ('uuid', 'label', 'version', 'status', 'date_created')

        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        # ...
        # Get last updated ExplainRevision
        # ...
        explain_params = dict()
        explain_fields = ('uuid', 'label', 'version', 'status', 'date_created')
        explain_revisions = ExplainRevision.objects \
            .filter(explain__guide__pk=OuterRef('guide__pk')) \
            .order_by('-date_updated')

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_explain=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Get last updated ChapterRevision
        # ...
        chapter_revisions = ChapterRevision.objects \
            .filter(chapter__guide__pk=OuterRef('guide__pk')) \
            .order_by('-date_updated')

        for item in chapter_fields:
            chapter_params['chapter_%s' % item] = Case(
                When(num_chapter=1, then=Subquery(chapter_revisions.values(item)[:1])),
                default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        try:
            revision = GuideRevision.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
                .select_related('creator', 'creator__user', 'guide') \
                .filter(uuid=uuid) \
                .annotate(
                    num_explain=Count('guide__explains', distinct=True),
                    num_chapter=Count('guide__chapters', distinct=True),
                    **explain_params,
                    **chapter_params) \
                .exclude(~Q(creator__pk=person_pk), ~Q(status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        # ...
        # Chapter annotate field
        # ...
        chapter_revisions = ChapterRevision.objects.filter(chapter__pk=OuterRef('pk'))

        for item in chapter_fields:
            chapter_params['chapter_%s' % item] = Case(
                When(num_revision=1, then=Subquery(chapter_revisions.values(item)[:1])),
                default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Count each status
        # ...
        explain_status_count = dict()
        for item in status_choices:
            status = item[0]
            explain_status_count['num_explain_%s' % status] = Count(
                'explains', distinct=True,
                filter=Q(explains__explain_revisions__status=status))

        # ...
        # Fetch all chapter based on GuideRevision
        # ...
        chapters = revision.guide.chapters \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .annotate(
                num_revision=Count('chapter_revisions', distinct=True),
                num_explain=Count('explains', distinct=True),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999
                ),
                **chapter_params,
                **explain_status_count) \
            .exclude(~Q(creator__pk=person_pk), ~Q(chapter_status=PUBLISHED)) \
            .order_by('sort_stage')

        # ...
        # Introductions
        # ...
        introductions = revision.introductions \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('content_type')) \
            .select_related('creator', 'creator__user', 'content_type') \
            .all()

        self.context['title'] = revision.label
        self.context['revision'] = revision
        self.context['revision_model_name'] = revision._meta.model_name
        self.context['introductions'] = introductions
        self.context['chapters'] = chapters
        self.context['status_choice'] = status_choices
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideEditorView(View):
    template_name = 'templates/guide/initial.html'
    context = dict()

    def get(self, request):
        categories_obj = Category.objects.all()

        self.context['title'] = _("Kirim Panduan")
        self.context['categories'] = categories_obj
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideRevisionEditorView(View):
    template_name = 'templates/guide/editor-revision.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]
        person = request.person

        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        try:
            revision_obj = GuideRevision.objects.get(
                uuid=uuid, creator=person)
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        self.context['revision'] = revision_obj
        self.context['title'] = revision_obj.label
        self.context['status_choice'] = status_choices
        return render(request, self.template_name, self.context)
