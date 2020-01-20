from django.db import transaction
from django.db.models import (
    F, When, Case, OuterRef, Subquery, Prefetch, Count, Q, Value,
    CharField)
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

# SERIALIZERS
from .serializers import ExplainSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')


class ExplainApiView(viewsets.ViewSet):
    """ Get attribute options for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        # Disable update if not owner
        'create': [IsAuthenticated, IsAllowCrudObject],
        'destroy': [IsAuthenticated, IsAllowCrudObject],
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action
                    [self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def list(self, request, format=None):
        context = {'request': self.request}
        params = request.query_params
        chapter_uuid = params.get('chapter_uuid', None)
        person = request.person
        person_pk = getattr(person, 'pk', None)

        chapter_uuid = check_uuid(uid=chapter_uuid)
        if not chapter_uuid:
            raise NotFound()

        explain_params = dict()
        explain_fields = ('pk', 'uuid', 'label', 'version', 'status')
        explain_revisions = ExplainRevision.objects.filter(explain__pk=OuterRef('pk'))

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_revision=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        queryset = Explain.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'),
                              Prefetch('chapter'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'chapter', 'guide') \
            .annotate(
                num_revision=Count('explain_revisions'),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999
                ),
                **explain_params) \
            .filter(chapter__uuid=chapter_uuid) \
            .exclude(~Q(creator__pk=person_pk), ~Q(explain_status=PUBLISHED)) \
            .order_by('sort_stage')
 
        serializer = ExplainSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = ExplainSerializer(data=request.data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Delete...
    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None):
        """uuid used uuid from attribute value"""
        uuid = check_uuid(uid=uuid)
        if not uuid:
            raise NotFound()

        person = request.person
        queryset = Explain.objects.filter(uuid=uuid, creator=person)

        if queryset.exists():
            queryset.delete()

        return Response(
            {'detail': _("Berhasil dihapus.")},
            status=response_status.HTTP_204_NO_CONTENT)

    # Sort stagte
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='sort', url_name='sort_stage')
    def sort_stage(self, request):
        person = request.person
        sortable = request.data.get('sortable', None)
        sortable_list = sortable.split(',')

        explain_list = list()
        explain_objs = Explain.objects.filter(
            pk__in=sortable_list, creator=person)

        if explain_objs.exists() and sortable_list:
            for index, item in enumerate(sortable_list, start=1):
                if item:
                    explain_obj = explain_objs.get(pk=item)
                    setattr(explain_obj, 'stage', index)
                    explain_list.append(explain_obj)

            Explain.objects.bulk_update(explain_list, ['stage'])
            return Response(status=response_status.HTTP_200_OK)
        raise NotFound()
