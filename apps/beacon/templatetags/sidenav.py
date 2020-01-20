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

ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')

register = template.Library()
template_chapter = get_template('templates/chapter/sidenav.html')
template_explain = get_template('templates/explain/sidenav.html')

def chapter_tree(request, revision):
    person_pk = request.person_pk

    # Chapters...
    chapter_params = dict()
    chapter_fields = ('uuid', 'label', 'status')
    chapter_revisions = ChapterRevision.objects.filter(chapter__pk=OuterRef('pk'))

    for item in chapter_fields:
        chapter_params['chapter_%s' % item] = Case(
            When(num_revision=1, then=Subquery(chapter_revisions.values(item)[:1])),
            default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1]))

    chapters = revision.chapter.guide.chapters \
        .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
        .select_related('creator', 'creator__user', 'guide') \
        .annotate(
            num_revision=Count('chapter_revisions'),
            sort_stage=Case(
                When(stage__isnull=False, then=F('stage')),
                default=99999
            ),
            **chapter_params) \
        .exclude(~Q(creator__pk=person_pk), ~Q(chapter_status=PUBLISHED)) \
        .order_by('sort_stage')

    # Explain...
    explain_params = dict()
    explain_fields = ('uuid', 'label', 'status')
    explain_revisions = ExplainRevision.objects.filter(explain__pk=OuterRef('pk'))

    for item in explain_fields:
        explain_params['explain_%s' % item] = Case(
            When(num_revision=1, then=Subquery(explain_revisions.values(item)[:1])),
            default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1]))

    for item in chapters:
        if item.uuid == revision.chapter.uuid:
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
                .exclude(~Q(creator__pk=person_pk), ~Q(explain_status=PUBLISHED)) \
                .order_by('sort_stage')
            item.explains_list = explains
    return chapters


def chapter_sidenav(request, revision, *args, **kwargs):
    chapters = chapter_tree(request, revision)
    return {'revision': revision, 'chapters': chapters}


def explain_sidenav(request, revision, explain, *args, **kwargs):
    chapters = chapter_tree(request, revision)
    return {'revision': revision, 'explain': explain, 'chapters': chapters}


register.inclusion_tag(template_chapter)(chapter_sidenav)
register.inclusion_tag(template_explain)(explain_sidenav)