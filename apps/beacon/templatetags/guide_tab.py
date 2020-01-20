#  Based on: http://www.djangosnippets.org/snippets/73/
#
#  Modified by Sean Reifschneider to be smarter about surrounding page
#  link context.  For usage documentation see:
#
#  http://www.tummy.com/Community/Articles/django-pagination/

from django import template
from django.http import Http404
from django.db.models import Prefetch, Count, Q
from django.core.exceptions import ObjectDoesNotExist

from utils.generals import get_model

register = template.Library()
GuideRevision = get_model('beacon', 'GuideRevision')


def guide_tab(request, guide_revision_uuid=None, identifier=None):
    person_pk = request.person_pk

    try:
        revision_obj = GuideRevision.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .filter(uuid=guide_revision_uuid, creator__pk=person_pk) \
            .annotate(
                num_explain=Count('guide__explains', distinct=True),
                num_chapter=Count('guide__chapters', distinct=True)) \
            .get()
    except ObjectDoesNotExist:
        raise Http404(_("Tidak ditemukan."))

    data = {
        'revision_obj': revision_obj,
        'guide_revision_uuid': guide_revision_uuid,
        'identifier': identifier
    }

    return data

register.inclusion_tag('dashboard/templates/guide_tab.html')(guide_tab)
