from django.views import View
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, F, Prefetch,
    CharField, Value, Q)
from django.http import Http404
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')


class ChapterRevisionDetailView(View):
    template_name = 'templates/chapter/detail.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        person = request.person
        person_pk = getattr(person, 'pk', None)
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        try:
            revision = ChapterRevision.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('chapter')) \
                .select_related('creator', 'creator__user', 'chapter') \
                .filter(uuid=uuid) \
                .exclude(~Q(creator__pk=person_pk), ~Q(status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        # Explain...
        explain_params = dict()
        explain_fields = ('pk', 'uuid', 'label', 'version', 'status')
        explain_revisions = ExplainRevision.objects.filter(explain__pk=OuterRef('pk'))

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_revision=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1]))

        explains = revision.chapter.explains \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('chapter')) \
            .select_related('creator', 'creator__user', 'chapter') \
            .annotate(
                num_revision=Count('explain_revisions'),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999
                ),
                **explain_params) \
            .exclude(~Q(creator__pk=person_pk), ~Q(explain_status=PUBLISHED)) \
            .order_by('sort_stage')

        self.context['title'] = revision.label
        self.context['revision'] = revision
        self.context['explains'] = explains
        self.context['status_choices'] = status_choices
        self.context['PUBLISHED'] = PUBLISHED
        self.context['DRAFT'] = DRAFT
        return render(request, self.template_name, self.context)
