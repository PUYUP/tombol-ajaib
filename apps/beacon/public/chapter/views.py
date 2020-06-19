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

Chapter = get_model('beacon', 'Chapter')
ChapterRevision = get_model('beacon', 'ChapterRevision')
Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')
EnrollmentChapter = get_model('beacon', 'EnrollmentChapter')
EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')


class ChapterDetailView(View):
    template_name = 'templates/chapter/detail.html'
    context = dict()

    def get(self, request, chapter_uuid=None):
        person = request.person
        person_pk = getattr(person, 'pk', None)
        status_choices = [item for item in STATUS_CHOICES if item[0] in [DRAFT, PUBLISHED]]

        chapter_uuid = check_uuid(uid=chapter_uuid)
        if not chapter_uuid:
            raise Http404(_("UUID invalid."))

        # ...
        # ChapterRevision objects in Subquery
        # ...
        revision_objs = ChapterRevision.objects.filter(chapter_id=OuterRef('id'))
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
        # Enrollment Guide
        # ...
        enrollment_guide_obj = EnrollmentGuide.objects \
            .filter(guide_id=OuterRef('guide_id'), creator_id=person_pk)

        # ...
        # Enrollment Chapter
        # ...
        enrollment_chapter_obj = EnrollmentChapter.objects \
            .filter(chapter_id=OuterRef('id'), creator_id=person_pk)

        try:
            queryset = Chapter.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide'),
                                  Prefetch('guide__category')) \
                .select_related('creator', 'creator__user', 'guide', 'guide__category') \
                .filter(uuid=chapter_uuid) \
                .annotate(
                    enrollment_guide_id=Subquery(enrollment_guide_obj.values('id')[:1]),
                    enrollment_chapter_id=Subquery(enrollment_chapter_obj.values('id')[:1]),
                    **draft_fields,
                    **published_fields) \
                .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        # Enroll!
        if queryset.enrollment_guide_id:
            # Enroll Chapter
            if not queryset.enrollment_chapter_id:
                queryset.enrollment_chapters \
                    .get_or_create(
                        creator_id=person_pk, enrollment_guide_id=queryset.enrollment_guide_id)

        # Create title
        title = queryset.draft_label
        if queryset.published_label:
            title = queryset.published_label

        # Explain List...
        revision_fields = ('id', 'uuid', 'label', 'version', 'status')
        revision_objs = ExplainRevision.objects.filter(explain_id=OuterRef('id'))

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

        explain_objs = queryset.explains \
            .prefetch_related(Prefetch('creator'), Prefetch('chapter')) \
            .select_related('creator', 'chapter') \
            .annotate(
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999),
                **draft_fields,
                **published_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED)) \
            .order_by('sort_stage', '-date_created')

        self.context['person_pk'] = person_pk
        self.context['title'] = title
        self.context['chapter_uuid'] = chapter_uuid
        self.context['chapter_obj'] = queryset
        self.context['explain_objs'] = explain_objs
        self.context['guide_obj'] = queryset.guide
        self.context['status_choices'] = status_choices
        self.context['PUBLISHED'] = PUBLISHED
        self.context['DRAFT'] = DRAFT
        # self.context['res'] = ero
        return render(request, self.template_name, self.context)
