#  Based on: http://www.djangosnippets.org/snippets/73/
#
#  Modified by Sean Reifschneider to be smarter about surrounding page
#  link context.  For usage documentation see:
#
#  http://www.tummy.com/Community/Articles/django-pagination/

from django import template

register = template.Library()


def proper_paginate(request, paginator, page_objs, neighbors=10):
    current_page = int(request.GET.get('page', 1))
    total_page = paginator.num_pages
    neighbors = int(neighbors)

    if total_page > 2*neighbors:
        start_index = max(1, current_page-neighbors)
        end_index = min(total_page, current_page + neighbors)

        if end_index < start_index + 2*neighbors:
            end_index = start_index + 2*neighbors
        elif start_index > end_index - 2*neighbors:
            start_index = end_index - 2*neighbors
        if start_index < 1:
            end_index -= start_index
            start_index = 1
        elif end_index > total_page:
            start_index -= (end_index-total_page)
            end_index = total_page

        page_list = [f for f in range(start_index, end_index+1)]
        return {'proper': page_list, 'page_objs': page_objs, 'total_page': total_page}
    return {'proper': paginator.page_range, 'page_objs': page_objs, 'total_page': total_page}

register.inclusion_tag('templates/paginator.html')(proper_paginate)
