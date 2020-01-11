from django.views import View
from django.db.models import Count, OuterRef, Subquery, Case, When
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from apps.beacon.utils.constant import (
    PUBLISHED, STATUS_CHOICES)

Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')


class HomeView(View):
    template_name = 'templates/home.html'
    context = dict()

    def get(self, request):
        revision_fields = ('uuid', 'label', 'date_updated', 'version', 'status')
        revision_params = dict()
        revisions = GuideRevision.objects.filter(guide__pk=OuterRef('pk'))

        for item in revision_fields:
            revision_params['revision_%s' % item] = Case(
                When(num_revision=1, then=Subquery(revisions.values(item)[:1])),
                default=Subquery(revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        guides = Guide.objects \
            .filter() \
            .annotate(
                num_revision=Count('guide_revisions'),
                **revision_params) \
            .order_by('-revision_date_updated')

        self.context['title'] = _("Beranda")
        self.context['guides'] = guides
        self.context['STATUS_CHOICES'] = STATUS_CHOICES
        return render(request, self.template_name, self.context)
