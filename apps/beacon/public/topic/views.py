from django.views import View
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, F, Prefetch,
    CharField, IntegerField, Value, Q, Sum, Exists)
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.contenttypes.models import ContentType

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')
Topic = get_model('beacon', 'Topic')
TopicRevision = get_model('beacon', 'TopicRevision')
GuideRevision = get_model('beacon', 'GuideRevision')


@method_decorator(login_required(login_url='login'), name='dispatch')
class TopicGuideListView(View):
    """ This case we show last revision based on Topic
    Use last published revision if more than one """
    template_name = 'templates/topic/list.html'
    context = dict()

    def get(self, request, guide_uuid=None):
        person_pk = request.person_pk
        revision_fields = ('uuid', 'label', 'date_updated', 'version', 'status')

        guide_uuid = check_uuid(uid=guide_uuid)
        if not guide_uuid:
            raise Http404(_("Guide UUID invalid."))

        try:
            enrollment_obj = EnrollmentGuide.objects \
                .get(guide__uuid=guide_uuid, creator_id=person_pk)
        except ObjectDoesNotExist:
            raise Http404(_("Enrollment invalid."))

        # ...
        # GuideRevision objects in Subquery
        # ...
        revision_guide_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))

        # ...
        # Collection for Guide Annotate
        # ...
        draft_guide_fields = dict()
        published_guide_fields = dict()

        for item in revision_fields:
            draft_guide_fields['draft_%s' % item] = Subquery(
                revision_guide_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_guide_fields['published_%s' % item] = Subquery(
                revision_guide_objs.filter(status=PUBLISHED).values(item)[:1])

        # ...
        # Run Guide query
        # ...
        try:
            enrolled_obj = enrollment_obj.guide._meta.model.objects \
                .prefetch_related(Prefetch('creator')) \
                .select_related('creator') \
                .annotate(
                    **draft_guide_fields,
                    **published_guide_fields) \
                .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
                .get(id=enrollment_obj.guide.id)
        except ObjectDoesNotExist:
            raise Http404(_("Access to Enrolled object rejected."))

        # ...
        # Collection for Annotate
        # ...
        revision_objs = TopicRevision.objects.filter(topic_id=OuterRef('pk'))

        draft_fields = dict()
        published_fields = dict()

        for item in revision_fields:
            draft_fields['draft_%s' % item] = Subquery(
                revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_fields['published_%s' % item] = Subquery(
                revision_objs.filter(status=PUBLISHED).values(item)[:1])

        model_name = enrollment_obj._meta.model_name
        content_type = ContentType.objects.get(app_label='beacon', model=model_name)

        topic_objs = Topic.objects \
            .prefetch_related(Prefetch('content_object'), Prefetch('content_type'), Prefetch('creator')) \
            .select_related('content_type', 'creator') \
            .filter(content_type=content_type.id, object_id=enrollment_obj.id) \
            .annotate(
                **draft_fields,
                **published_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
        
        # Create title
        title = enrolled_obj.draft_label
        if enrolled_obj.published_label:
            title = enrolled_obj.published_label

        self.context['title'] = _("Topik %s" % title)
        self.context['enrolled_obj'] = enrolled_obj
        self.context['topic_objs'] = topic_objs
        self.context['STATUS_CHOICES'] = STATUS_CHOICES
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class TopicGuideDetailView(View):
    template_name = 'templates/topic/detail.html'
    context = dict()

    def get(self, request, guide_uuid=None, topic_uuid=None):
        person_pk = request.person_pk
        revision_fields = ('uuid', 'label', 'date_updated', 'version', 'status')

        guide_uuid = check_uuid(uid=guide_uuid)
        if not guide_uuid:
            raise Http404(_("Guide UUID invalid."))

        topic_uuid = check_uuid(uid=topic_uuid)
        if not topic_uuid:
            raise Http404(_("Topic UUID invalid."))

        try:
            enrollment_obj = EnrollmentGuide.objects \
                .get(guide__uuid=guide_uuid, creator_id=person_pk)
        except ObjectDoesNotExist:
            raise Http404(_("Enrollment invalid."))

        # ...
        # GuideRevision objects in Subquery
        # ...
        revision_guide_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))

        # ...
        # Collection for Guide Annotate
        # ...
        draft_guide_fields = dict()
        published_guide_fields = dict()

        for item in revision_fields:
            draft_guide_fields['draft_%s' % item] = Subquery(
                revision_guide_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_guide_fields['published_%s' % item] = Subquery(
                revision_guide_objs.filter(status=PUBLISHED).values(item)[:1])

        # ...
        # Run Guide query
        # ...
        enrolled_obj = enrollment_obj.guide._meta.model.objects \
            .prefetch_related(Prefetch('creator')) \
            .select_related('creator') \
            .annotate(
                **draft_guide_fields,
                **published_guide_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
            .get(id=enrollment_obj.guide.id)

        # ...
        # Collection for Annotate
        # ...
        revision_objs = TopicRevision.objects.filter(topic_id=OuterRef('pk'))

        draft_fields = dict()
        published_fields = dict()

        for item in revision_fields:
            draft_fields['draft_%s' % item] = Subquery(
                revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_fields['published_%s' % item] = Subquery(
                revision_objs.filter(status=PUBLISHED).values(item)[:1])

        model_name = enrollment_obj._meta.model_name
        content_type = ContentType.objects.get(app_label='beacon', model=model_name)

        topic_obj = Topic.objects \
            .filter(content_type=content_type.id, object_id=enrollment_obj.id) \
            .annotate(
                **draft_fields,
                **published_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
            .get(uuid=topic_uuid)

        # Create title
        title = topic_obj.draft_label
        if topic_obj.published_label:
            title = topic_obj.published_label

        self.context['title'] = title
        self.context['enrolled_obj'] = enrolled_obj
        self.context['topic_obj'] = topic_obj
        self.context['STATUS_CHOICES'] = STATUS_CHOICES
        return render(request, self.template_name, self.context)


"""
class GuideDetailView(View):
    template_name = 'templates/guide/detail.html'
    context = dict()

    def get(self, request, guide_uuid=None):
        introduction_draft_objs = None
        person_pk = request.person_pk
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        guide_uuid = check_uuid(uid=guide_uuid)
        if not guide_uuid:
            raise Http404(_("Guide UUID invalid."))

        # ...
        # GuideRevision objects in Subquery
        # ...
        revision_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))
        revision_fields = ('id', 'uuid', 'label', 'version', 'status',
                           'date_created', 'date_updated', 'description', 'changelog')

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
        # Enrollment query
        # ...
        enrollment_guide_obj = EnrollmentGuide.objects \
            .filter(guide_id=OuterRef('id'), creator_id=person_pk)

        # ...
        # Run query
        # ...
        try:
            queryset = Guide.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('category')) \
                .select_related('creator', 'creator__user', 'category') \
                .filter(Q(uuid=guide_uuid) | Q(guide_revisions__uuid=guide_uuid)) \
                .annotate(
                    num_revision=Count('guide_revisions', distinct=True),
                    num_explain=Count('explains', distinct=True),
                    num_chapter=Count('chapters', distinct=True),
                    enrollment_guide_uuid=Subquery(enrollment_guide_obj.values('uuid')[:1]),
                    **draft_fields,
                    **published_fields) \
                .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Not found."))

        # ...
        # Introductions
        # ...
        content_type = ContentType.objects.get_for_model(GuideRevision)
        introduction_objs = Introduction.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('content_type')) \
            .select_related('creator', 'creator__user', 'content_type') \
            .filter(content_type=content_type)

        if queryset.creator.id == person_pk:
            introduction_draft_objs = introduction_objs.filter(object_id=queryset.draft_id)
        introduction_published_objs = introduction_objs.filter(object_id=queryset.published_id)

        # Create title
        title = queryset.draft_label
        if queryset.published_label:
            title = queryset.published_label

        self.context['person_pk'] = person_pk
        self.context['guide_uuid'] = guide_uuid
        self.context['guide_obj'] = queryset
        self.context['title'] = title
        self.context['introduction_draft_objs'] = introduction_draft_objs
        self.context['introduction_published_objs'] = introduction_published_objs
        self.context['content_type'] = content_type
        self.context['status_choices'] = status_choices
        self.context['DRAFT'] = DRAFT
        self.context['PUBLISHED'] = PUBLISHED
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideSortingView(View):
    template_name = 'templates/guide/sorting.html'
    context = dict()

    def get(self, request, guide_uuid=None):
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]
        person_pk = request.person_pk

        guide_uuid = check_uuid(uid=guide_uuid)
        if not guide_uuid:
            raise Http404(_("Guide UUID invalid."))

        # ...
        # GuideRevision objects in Subquery
        # ...
        revision_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))
        revision_fields = ('id', 'uuid', 'label', 'version', 'status',
                           'date_created', 'date_updated', 'description', 'changelog')

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
                .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Not found."))

        if queryset.creator.id is not person_pk:
            raise PermissionDenied()

        # Create title
        title = queryset.draft_label
        if queryset.published_label:
            title = queryset.published_label

        self.context['guide_uuid'] = guide_uuid
        self.context['guide_obj'] = queryset
        self.context['title'] = title
        self.context['status_choices'] = status_choices
        return render(request, self.template_name, self.context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class GuideInitialView(View):
    template_name = 'templates/guide/initial.html'
    context = dict()

    def get(self, request):
        category_objs = Category.objects.all()

        self.context['title'] = _("Mulai Panduan")
        self.context['category_objs'] = category_objs
        return render(request, self.template_name, self.context)
"""
