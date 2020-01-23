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


def guide_tab(context):
    return context

register.inclusion_tag('dashboard/templates/guide_tab.html', takes_context=True)(guide_tab)
