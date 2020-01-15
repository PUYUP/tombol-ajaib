from django.views import View
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, F, Prefetch,
    CharField, Value, Q)
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import render, redirect, reverse
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
ExplainRevision = get_model('beacon', 'ExplainRevision')


class GuideListView(View):
    """ This case we show last revision based on Guide
    Use last published revision if more than one """
    template_name = 'templates/guide/list.html'
    context = dict()

    def get(self, request):
        revision_fields = ('uuid', 'label', 'date_updated', 'version', 'status')
        revision_params = dict()
        person = getattr(request.user, 'person', None)
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
        person = getattr(request.user, 'person', None)
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))
        
        # Filter guides status
        # If creator show PUBLISHED and DRAFT
        # If other user only PUBLISHED
        status_for_guide_creator = list()
        for item in status_choices:
            status = item[0]
            status_when = When(Q(creator=person) & Q(status=status), then=Value(status))
            status_for_guide_creator.append(status_when)

        try:
            revision = GuideRevision.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
                .select_related('creator', 'creator__user', 'guide') \
                .filter(
                    uuid=uuid,
                    status=Case(
                        *status_for_guide_creator,
                        output_field=CharField(),
                        default=Value(PUBLISHED)
                    )
                ).get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        introductions = revision.introductions \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('content_type')) \
            .select_related('creator', 'creator__user', 'content_type') \
            .all()

        # Chapters...
        chapter_params = dict()
        chapter_fields = ('pk', 'uuid', 'label', 'description', 'version', 'status')
        chapter_revisions = ChapterRevision.objects.filter(chapter__pk=OuterRef('pk'))

        for item in chapter_fields:
            chapter_params['chapter_%s' % item] = Case(
                When(num_revision=1, then=Subquery(chapter_revisions.values(item)[:1])),
                default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # Filter chapters status
        # If creator show PUBLISHED and DRAFT
        # If other user only PUBLISHED
        status_for_chapter_creator = list()
        for item in status_choices:
            status = item[0]
            status_when = When(Q(creator=person) & Q(chapter_status=status), then=Value(status))
            status_for_chapter_creator.append(status_when)

        chapters = revision.guide.chapters \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .annotate(
                num_revision=Count('chapter_revisions'),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999
                ),
                **chapter_params) \
            .filter(
                chapter_status=Case(
                    *status_for_chapter_creator,
                    output_field=CharField(),
                    default=Value(PUBLISHED)
                )) \
            .order_by('sort_stage')

        # Explain...
        """
        NOT USED, BUT KEEP IT FOR INSPIRATION
        explain_params = dict()
        explain_fields = ('pk', 'uuid', 'label', 'version', 'status')
        explain_revisions = ExplainRevision.objects.filter(explain__pk=OuterRef('pk'))

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_revision=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        for item in chapters:
            explains = item.explains \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('chapter')) \
                .select_related('creator', 'creator__user', 'chapter') \
                .annotate(
                    num_revision=Count('explain_revisions'),
                    sort_stage=Case(
                        When(stage__isnull=False, then=F('stage')),
                        default=99999
                    ),
                    **explain_params) \
                .order_by('sort_stage')
            item.explains_list = explains
        """

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
        person = getattr(request.user, 'person', None)
        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        try:
            revision_obj = GuideRevision.objects.get(
                uuid=uuid, creator=person)
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        # only allow edit if DRAFT
        if revision_obj.status is not DRAFT:
            try:
                revision_published_obj = GuideRevision.objects.get(
                    guide__uuid=revision_obj.guide.uuid, creator=person,
                    status=PUBLISHED)
            except ObjectDoesNotExist:
                revision_published_obj = None

        self.context['revision'] = revision_obj
        self.context['revision_published'] = revision_published_obj
        self.context['title'] = revision_obj.label
        self.context['status_choice'] = status_choices
        return render(request, self.template_name, self.context)
