from django import template
from django.template.loader import get_template

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


def chapter_tree(context):
    person_pk = context['person_pk']
    guide_uuid = context['guide_uuid']
    revision_fields = ('uuid', 'label', 'version', 'status', 'date_created')

    # ...
    # ChapterRevision objects in Subquery
    # ...
    chapter_draft_fields = dict()
    chapter_published_fields = dict()
    chapter_revision_objs = ChapterRevision.objects.filter(chapter_id=OuterRef('chapter_id'))

    for item in revision_fields:
        chapter_draft_fields['chapter_draft_%s' % item] = Subquery(
            chapter_revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

        chapter_published_fields['chapter_published_%s' % item] = Subquery(
            chapter_revision_objs.filter(status=PUBLISHED).values(item)[:1])

    # ...
    # ExplainRevision objects in Subquery
    # ...
    explain_draft_fields = dict()
    explain_published_fields = dict()
    explain_revision_objs = ExplainRevision.objects.filter(explain_id=OuterRef('id'))

    for item in revision_fields:
        explain_draft_fields['explain_draft_%s' % item] = Subquery(
            explain_revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

        explain_published_fields['explain_published_%s' % item] = Subquery(
            explain_revision_objs.filter(status=PUBLISHED).values(item)[:1])

    explain_objs = Explain.objects \
        .prefetch_related(Prefetch('creator'), Prefetch('guide'), Prefetch('chapter')) \
        .select_related('creator', 'guide', 'chapter') \
        .filter(guide__uuid=guide_uuid) \
        .annotate(
            sort_stage=Case(
                When(chapter__stage__isnull=False, then=F('chapter__stage')),
                default=99999),
            **chapter_draft_fields,
            **chapter_published_fields,
            **explain_draft_fields,
            **explain_published_fields) \
        .order_by('sort_stage', 'chapter__date_created') \
        .exclude(~Q(chapter__creator_id=person_pk), ~Q(chapter_published_status=PUBLISHED))

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
    chapter_draft_fields = dict()
    chapter_published_fields = dict()
    chapter_revision_objs = ChapterRevision.objects.filter(chapter_id=OuterRef('id'))

    for item in revision_fields:
        chapter_draft_fields['chapter_draft_%s' % item] = Subquery(
            chapter_revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

        chapter_published_fields['chapter_published_%s' % item] = Subquery(
            chapter_revision_objs.filter(status=PUBLISHED).values(item)[:1])

    chapter_objs = Chapter.objects \
        .prefetch_related('guide') \
        .select_related('guide') \
        .filter(guide__uuid=guide_uuid) \
        .annotate(
            **chapter_draft_fields,
            **chapter_published_fields,
            sort_stage=Case(
                When(stage__isnull=False, then=F('stage')),
                default=99999)) \
        .order_by('sort_stage', 'date_created') \
        .exclude(~Q(creator_id=person_pk), ~Q(chapter_published_status=PUBLISHED))

    for item in chapter_objs:
        res.setdefault(item, [])

    eri = sorted(res.items(), key=lambda item: item[0].sort_stage)
    trees = {k: v for k, v in eri}
    return {'trees': trees}


register = template.Library()
template_name = get_template('templates/chapter/tree.html')
register.inclusion_tag(template_name, takes_context=True)(chapter_tree)
