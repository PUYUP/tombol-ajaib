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

ExplainRevision = get_model('beacon', 'ExplainRevision')


@method_decorator(login_required(login_url='login'), name='dispatch')
class ExplainRevisionEditorView(View):
    template_name = 'templates/explain/editor-revision.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        person = request.person
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        try:
            revision_obj = ExplainRevision.objects.get(
                uuid=uuid, creator=person)
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        content = None
        blob = getattr(revision_obj.content, 'blob', None)

        if blob:
            content = blob.decode('utf-8')

        self.context['title'] = _("Perbarui Isi Sub-bab")
        self.context['revision'] = revision_obj
        self.context['content'] = content
        self.context['status_choice'] = status_choices
        return render(request, self.template_name, self.context)


class ExplainRevisionDetailView(View):
    template_name = 'templates/explain/detail.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        person = request.person
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        # Filter explains status
        # If creator show PUBLISHED and DRAFT
        # If other user only PUBLISHED
        status_for_explain_creator = list()
        for item in status_choices:
            status = item[0]
            status_when = When(Q(creator=person) & Q(status=status), then=Value(status))
            status_for_explain_creator.append(status_when)

        try:
            revision = ExplainRevision.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('explain')) \
                .select_related('creator', 'creator__user', 'explain') \
                .filter(
                    uuid=uuid,
                    status=Case(
                        *status_for_explain_creator,
                        output_field=CharField(),
                        default=Value(PUBLISHED)
                    )
                ).get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        content = None
        blob = getattr(revision.content, 'blob', None)

        if blob:
            content = blob.decode('utf-8')
    
        self.context['title'] = revision.label
        self.context['revision'] = revision
        self.context['explain'] = revision.explain
        self.context['content'] = content
        self.context['PUBLISHED'] = PUBLISHED
        self.context['DRAFT'] = DRAFT
        return render(request, self.template_name, self.context)
