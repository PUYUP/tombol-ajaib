from django.views import View


class ChapterView(View):
    template_name = 'templates/chapter/detail.html'
    context = dict()
