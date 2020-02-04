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
        person_pk = request.person_pk
        revision_fields = ('uuid', 'label', 'date_updated', 'version', 'status')
        revision_params = dict()
        revisions = GuideRevision.objects.filter(guide_id=OuterRef('pk'))

        for item in revision_fields:
            revision_params['revision_%s' % item] = Case(
                When(num_revision=1, then=Subquery(revisions.values(item)[:1])),
                default=Subquery(revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        guides = Guide.objects \
            .annotate(
                num_revision=Count('guide_revisions'),
                **revision_params) \
            .order_by('-revision_date_updated') \
            .exclude(~Q(creator_id=person_pk), ~Q(revision_status=PUBLISHED))

        category_objs = Category.objects.all()

        self.context['title'] = _("Beranda")
        self.context['guides'] = guides
        self.context['category_objs'] = category_objs
        return render(request, self.template_name, self.context)
