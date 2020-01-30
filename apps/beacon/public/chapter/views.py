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


class ChapterRevisionDetailView(View):
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
        revision_objs = ChapterRevision.objects.filter(chapter__id=OuterRef('chapter__id'))
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

        try:
            queryset = ChapterRevision.objects \
                .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('chapter'), Prefetch('guide')) \
                .select_related('creator', 'creator__user', 'chapter', 'guide') \
                .filter(uuid=chapter_uuid) \
                .annotate(
                    **draft_fields,
                    **published_fields) \
                .exclude(~Q(creator__id=person_pk), ~Q(status=PUBLISHED)) \
                .get()
        except ObjectDoesNotExist:
            raise Http404(_("Tidak ditemukan."))

        # ...
        # ChapterRevision objects in Subquery
        # ...
        revision_objs = ChapterRevision.objects.filter(chapter__id=OuterRef('chapter__id'))
        revision_fields = ('uuid', 'label', 'version', 'status', 'date_created')

        # ...
        # Collection fro Annotate
        # ...
        draft_fields = dict()
        published_fields = dict()

        for item in revision_fields:
            draft_fields['chapter_draft_%s' % item] = Subquery(
                revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_fields['chapter_published_%s' % item] = Subquery(
                revision_objs.filter(status=PUBLISHED).values(item)[:1])

        # ...
        # ExplainRevision objects in Subquery
        # ...
        explain_revision_objs = ExplainRevision.objects.filter(explain_id=OuterRef('id'))
        explain_revision_fields = ('uuid', 'label', 'version', 'status', 'date_created')

        # ...
        # Collection fro Annotate
        # ...
        explain_draft_fields = dict()
        explain_published_fields = dict()

        for item in explain_revision_fields:
            explain_draft_fields['explain_draft_%s' % item] = Subquery(
                explain_revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            explain_published_fields['explain_published_%s' % item] = Subquery(
                explain_revision_objs.filter(status=PUBLISHED).values(item)[:1])

        explain_objs = Explain.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('guide'), Prefetch('chapter')) \
            .select_related('creator', 'guide', 'chapter') \
            .filter(guide__id=queryset.guide.id) \
            .annotate(
                sort_stage=Case(
                    When(chapter__stage__isnull=False, then=F('chapter__stage')),
                    default=99999),
                **draft_fields,
                **published_fields,
                **explain_draft_fields,
                **explain_published_fields) \
            .order_by('sort_stage', 'chapter__date_created') \
            .exclude(~Q(chapter__creator__id=person_pk), ~Q(chapter_published_status=PUBLISHED))

        res = {}
        for item in explain_objs:
            chapter = item.chapter

            for rev_field in revision_fields:
                setattr(chapter, 'chapter_draft_%s' % rev_field, getattr(item, 'chapter_draft_%s' % rev_field))
                setattr(chapter, 'chapter_published_%s' % rev_field, getattr(item, 'chapter_published_%s' % rev_field))
                setattr(chapter, 'sort_stage', item.sort_stage)

            if item.creator.id != person_pk and item.explain_published_status == PUBLISHED:
                res.setdefault(chapter, []).append(item)
            elif item.creator.id == person_pk:
                res.setdefault(chapter, []).append(item)

        # ...
        # ChapterRevision objects in Subquery
        # ...
        revision_objs = ChapterRevision.objects.filter(chapter__id=OuterRef('id'))
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
    
        x = Chapter.objects \
            .prefetch_related('guide') \
            .select_related('guide') \
            .filter(guide__id=queryset.guide.id) \
            .annotate(
                **draft_fields,
                **published_fields,
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999)) \
            .order_by('sort_stage', 'date_created') \
            .exclude(~Q(creator__id=person_pk), ~Q(published_status=PUBLISHED))

        for item in x:
            res.setdefault(item, [])

        eri = sorted(res.items(), key=lambda item: item[0].sort_stage)
        ero = {k: v for k, v in eri}
        print(ero)
        ema = {}
        hma = []
        for key, value in res.items():
            ema = {
                'sort_stage': key.sort_stage,
                'chapter': key,
                'explains': value
            }
            hma.append(ema)
        
        unit_list = sorted(hma, key = lambda i: i['sort_stage'])

        self.context['title'] = queryset.label
        self.context['chapter_uuid'] = chapter_uuid
        self.context['chapter_obj'] = queryset
        self.context['status_choices'] = status_choices
        self.context['PUBLISHED'] = PUBLISHED
        self.context['DRAFT'] = DRAFT
        self.context['res'] = ero
        self.context['unit_list'] = unit_list
        return render(request, self.template_name, self.context)
