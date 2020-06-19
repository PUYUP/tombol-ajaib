from django.views import View
from django.db.models import Count, OuterRef, Subquery, Case, When, Q, Prefetch
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from apps.beacon.utils.constant import PUBLISHED

Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')
Category = get_model('beacon', 'Category')


class HomeView(View):
    template_name = 'templates/page/home.html'
    context = dict()

    def get(self, request):
        category_objs = Category.objects \
            .annotate(
                guide_count=Count('pk', filter=Q(guides__guide_revisions__status=PUBLISHED))) \
            .all()

        obj = GuideRevision.objects.get(id=504)
        # obj.pk = None
        # obj.save()

        print(obj.introductions.all())

        self.context['title'] = _("Beranda")
        self.context['category_objs'] = category_objs
        return render(request, self.template_name, self.context)
