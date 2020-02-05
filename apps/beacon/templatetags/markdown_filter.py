import markdown
from django import template

register = template.Library()


@register.filter
def markdownify(value):
    print('LOCK')
    return markdown.markdown(value, safe_mode='escape')
