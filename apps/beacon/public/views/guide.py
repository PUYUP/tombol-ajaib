from django.views import View
from django.db.models import Count, OuterRef, Subquery, Case, When
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

        self.context['title'] = _("Daftar Tutorial")
        self.context['guides'] = guides
        self.context['STATUS_CHOICES'] = STATUS_CHOICES
        return render(request, self.template_name, self.context)


class GuideRevisionDetailView(View):
    template_name = 'templates/guide/detail.html'
    context = dict()

    def get(self, request, revision_uuid=None):
        uuid = check_uuid(uid=revision_uuid)
        if not uuid:
            raise Http404(_("Tidak ditemukan."))

        try:
            revision = GuideRevision.objects \
                .prefetch_related('creator', 'creator__user', 'guide') \
                .select_related('creator', 'creator__user', 'guide') \
                .filter(uuid=uuid).get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        introductions = revision.introductions \
            .prefetch_related('creator', 'creator__user', 'content_type') \
            .select_related('creator', 'creator__user', 'content_type') \
            .all()

        self.context['title'] = revision.label
        self.context['revision'] = revision
        self.context['revisio_model_name'] = revision._meta.model_name
        self.context['introductions'] = introductions
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideEditorView(View):
    template_name = 'templates/guide/initial.html'
    context = dict()

    def get(self, request):
        categories_obj = Category.objects.all()

        self.context['title'] = _("Kirim Tutorial")
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
