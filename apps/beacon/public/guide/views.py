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

    def get(self, request, guide_uuid=None):
        person_pk = request.person_pk
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        guide_uuid = check_uuid(uid=guide_uuid)
        if not guide_uuid:
            raise Http404(_("Guide UUID invalid."))

        # ...
        # GudeRevision objects in Subquery
        # ...
        revision_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))
        revision_fields = ('uuid', 'label', 'version', 'status', 'date_created')

        # ...
        # Collection fro Annotate
        # ...
        draft_fields = dict()
        published_fields = dict()

        for item in revision_fields:
            draft_fields['draft_%s' % item] = Subquery(
                revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_fields['published_%s' % item] = Subquery(
                revision_objs.filter(status=PUBLISHED).values(item)[:1])

        # ...
        # Run query
        # ...
        try:
            queryset = Guide.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user')) \
                .select_related('creator', 'creator__user') \
                .filter(Q(uuid=guide_uuid) | Q(guide_revisions__uuid=guide_uuid)) \
                .annotate(
                    num_revision=Count('guide_revisions', distinct=True),
                    num_explain=Count('explains', distinct=True),
                    num_chapter=Count('chapters', distinct=True),
                    **draft_fields,
                    **published_fields) \
                .exclude(~Q(creator__id=person_pk), ~Q(published_status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Not found."))

        self.context['person_pk'] = person_pk
        self.context['guide_uuid'] = guide_uuid
        self.context['guide_obj'] = queryset
        self.context['title'] = queryset.label
        self.context['status_choices'] = status_choices
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
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
        self.context['status_choices'] = status_choices
        return render(request, self.template_name, self.context)
