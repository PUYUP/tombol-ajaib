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
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import SheetSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Sheet = get_model('beacon', 'Sheet')
SheetRevision = get_model('beacon', 'SheetRevision')


class SheetApiView(viewsets.ViewSet):
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
        """ Can use 'guide_uuid' """
        context = {'request': self.request}
        params = request.query_params
        person_pk = request.person_pk
        person_uuid = params.get('person_uuid', None)

        guide_uuid = params.get('guide_uuid', None)
        guide_uuid = check_uuid(uid=guide_uuid)

        if not guide_uuid:
            raise NotAcceptable(detail=_("Guide UUID invalid."))

        # Person UUID defined
        if person_uuid:
            person_uuid = check_uuid(uid=person_uuid)

            if not person_uuid:
                raise NotAcceptable(detail=_("Person UUID invalid."))

        # ...
        # SheetRevision objects in Subquery
        # ...
        revision_objs = SheetRevision.objects.filter(sheet_id=OuterRef('id'))
        revision_fields = ('uuid', 'label', 'version', 'status', 'date_created')

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

        queryset = Sheet.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .filter(Q(guide__uuid=guide_uuid) | Q(guide__guide_revisions__uuid=guide_uuid)) \
            .annotate(
                num_revision=Count('sheet_revisions', distinct=True),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999
                ),
                **draft_fields,
                **published_fields) \
            .order_by('sort_stage') \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED))

        if person_uuid:
            queryset = queryset.filter(creator__uuid=person_uuid)

        if not queryset.exists():
            raise NotFound(_("Not found."))

        serializer = SheetSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = SheetSerializer(data=request.data, context=context)

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
        queryset = Sheet.objects.filter(uuid=uuid, creator=person)

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

        sheet_list = list()
        sheet_objs = Sheet.objects.filter(
            pk__in=sortable_list, creator=person)

        if sheet_objs.exists() and sortable_list:
            for index, item in enumerate(sortable_list, start=1):
                if item:
                    sheet_obj = sheet_objs.get(pk=item)
                    setattr(sheet_obj, 'stage', index)
                    sheet_list.append(sheet_obj)

            Sheet.objects.bulk_update(sheet_list, ['stage'])
            return Response(status=response_status.HTTP_200_OK)
        raise NotFound()
