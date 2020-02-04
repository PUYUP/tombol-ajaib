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

Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')
Content = get_model('beacon', 'Content')


@method_decorator(login_required(login_url='login'), name='dispatch')
class ExplainEditorView(View):
    template_name = 'templates/explain/editor-revision.html'
    context = dict()

    def get(self, request, explain_uuid=None):
        person = request.person
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        uuid = check_uuid(uid=explain_uuid)
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


class ExplainDetailView(View):
    template_name = 'templates/explain/detail.html'
    context = dict()

    def get(self, request, explain_uuid=None):
        person_pk = request.person_pk
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        explain_uuid = check_uuid(uid=explain_uuid)
        if not explain_uuid:
            raise Http404(_("UUID invalid."))

        # ...
        # ExplainRevision objects in Subquery
        # ...
        revision_objs = ExplainRevision.objects.filter(explain_id=OuterRef('id'))
        revision_fields = ('uuid', 'label', 'version', 'status', 'date_created',
                           'date_updated', 'content', 'changelog')

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

        try:
            queryset = Explain.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide'),
                                  Prefetch('guide__category')) \
                .select_related('creator', 'creator__user', 'guide', 'guide__category') \
                .filter(uuid=explain_uuid) \
                .annotate(
                    **draft_fields,
                    **published_fields) \
                .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))
        
        # Create title
        title = queryset.draft_label
        if queryset.published_label:
            title = queryset.published_label

        # Content Object DRAFT
        content_draft = None
        content_draft_pk = queryset.draft_content

        if content_draft_pk:
            try:
                content_draft_obj = Content.objects.get(id=content_draft_pk)
                blob = getattr(content_draft_obj, 'blob', None)
            except ObjectDoesNotExist:
                content_draft_obj = None

            if content_draft_obj and blob:
                if type(blob) is memoryview:
                    mv = memoryview(blob)
                    content_draft = mv.tobytes().decode('utf-8')
                else:
                    content_draft = blob.decode('utf-8')

        # Content Object PUBLISHED
        content_published = None
        content_published_pk = queryset.published_content

        if content_published_pk:
            try:
                content_published_obj = Content.objects.get(id=content_published_pk)
                blob = getattr(content_published_obj, 'blob', None)
            except ObjectDoesNotExist:
                content_published_obj = None

            if content_published_obj and blob:
                if type(blob) is memoryview:
                    mv = memoryview(blob)
                    content_published = mv.tobytes().decode('utf-8')
                else:
                    content_published = blob.decode('utf-8')

        self.context['person_pk'] = person_pk
        self.context['title'] = title
        self.context['explain_uuid'] = explain_uuid
        self.context['explain_obj'] = queryset
        self.context['guide_obj'] = queryset.guide
        self.context['content_draft'] = content_draft
        self.context['content_published'] = content_published
        self.context['PUBLISHED'] = PUBLISHED
        self.context['DRAFT'] = DRAFT
        self.context['status_choices'] = status_choices
        return render(request, self.template_name, self.context)
