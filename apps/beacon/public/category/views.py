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

Category = get_model('beacon', 'Category')
Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')


class CategoryGuideListView(View):
    template_name = 'templates/category/guide-list.html'
    context = dict()

    def get(self, request, category_uuid=None):
        person_pk = request.person_pk
        category_uuid = check_uuid(uid=category_uuid)

        if not category_uuid:
            raise Http404()

        # ...
        # GuideRevision objects in Subquery
        # ...
        revision_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))
        revision_fields = ('uuid', 'label', 'version', 'status', 'date_updated')

        # ...
        # Collection fro Annotate
        # ...
        draft_fields = dict()
        published_fields = dict()

        for item in revision_fields:
            draft_fields['draft_%s' % item] = Subquery(
                revision_objs.filter(status=DRAFT).order_by('-version').values(item)[:1])

            published_fields['published_%s' % item] = Subquery(
                revision_objs.filter(status=PUBLISHED).values(item)[:1])

        # ...
        # Run query
        # ...
        guide_objs = Guide.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('category')) \
            .select_related('creator', 'creator__user', 'category') \
            .filter(category__uuid=category_uuid) \
            .annotate(
                num_explain=Count('explains', distinct=True),
                num_chapter=Count('chapters', distinct=True),
                **draft_fields,
                **published_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED))

        try:
            category_obj = Category.objects.get(uuid=category_uuid)
        except ObjectDoesNotExist:
            raise Http404()

        self.context['title'] = _("Kategori %s" % category_obj.label)
        self.context['guide_objs'] = guide_objs
        self.context['category_obj'] = category_obj
        return render(request, self.template_name, self.context)
