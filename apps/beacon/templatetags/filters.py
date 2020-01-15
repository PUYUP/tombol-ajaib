from django import template
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, F, Prefetch,
    CharField, Value, Q)

register = template.Library()

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)


@register.filter
def xxx(value, arg):
    person = arg.get('person', None)
    status_choices = arg.get('status_choices', None)
    status_for_guide_creatory = list()

    for item in status_choices:
        status = item[0]
        status_when = When(Q(creator=person) & Q(chapter__chapter_revisions__status=status), then=Value(status))
        status_for_guide_creatory.append(status_when)

    value = value.filter(
        chapter__chapter_revisions__status=Case(
            *status_for_guide_creatory,
            output_field=CharField(),
            default=Value(PUBLISHED)
        )).distinct()

    return value


@register.filter
def yyy(value, arg):
    """
    person = arg.get('person', None)
    status_choices = arg.get('status_choices', None)
    status_for_guide_creatorx = list()

    for item in status_choices:
        status = item[0]
        status_when = When(Q(creator=person) & Q(explain_revisions__status=status), then=Value(status))
        status_for_guide_creatorx.append(status_when)

    value = value.filter(
        explain_revisions__status=Case(
            *status_for_guide_creatorx,
            output_field=CharField(),
            default=Value(PUBLISHED)
        )).distinct()
    """
    print(value)
    return value
