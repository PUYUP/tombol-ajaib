from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, Prefetch, Q)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.pagination import PageNumberPagination

# SERIALIZERS
from .serializers import GuideSerializer, GuideListSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# # PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')
ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


class GuideApiView(viewsets.ViewSet):
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

        person_pk = request.person_pk
        person_uuid = params.get('person_uuid', None)

        # Person UUID defined
        if person_uuid:
            person_uuid = check_uuid(uid=person_uuid)

            if not person_uuid:
                raise NotAcceptable(detail=_("Person UUID invalid."))

        # ...
        # GudeRevision objects in Subquery
        # ...
        revision_objs = GuideRevision.objects.filter(guide_id=OuterRef('id'))
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

        # ...
        # Run query
        # ...
        queryset = Guide.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user')) \
            .select_related('creator', 'creator__user') \
            .annotate(
                num_revision=Count('guide_revisions', distinct=True),
                num_explain=Count('explains', distinct=True),
                num_chapter=Count('chapters', distinct=True),
                **draft_fields,
                **published_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED))

        if person_uuid:
            queryset = queryset.filter(creator__uuid=person_uuid)

        if not queryset.exists():
            raise NotFound(_("Not found."))

        queryset_paginate = PAGINATOR.paginate_queryset(queryset, request)
        serializer = GuideListSerializer(queryset_paginate, many=True, context=context)

        response = {
            'count': PAGINATOR.page.paginator.count,
            'navigate': {
                'previous': PAGINATOR.get_previous_link(),
                'next': PAGINATOR.get_next_link()
            },
            'results': serializer.data
        }

        return Response(response, status=response_status.HTTP_200_OK)

    # Return a response
    def get_response(self, serializer, serializer_parent=None, *args, **kwargs):
        """ Output to endpoint """
        response = dict()
        limit = kwargs.get('limit', None)

        if serializer.data and limit:
            response['count'] = int(limit)

        if not limit:
            if serializer_parent is not None:
                response['media'] = serializer_parent.data

            response['count'] = PAGINATOR.page.paginator.count
            response['navigate'] = {
                'previous': PAGINATOR.get_previous_link(),
                'next': PAGINATOR.get_next_link()
            }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = GuideSerializer(data=request.data, context=context)

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
        queryset = Guide.objects.filter(uuid=uuid, creator=person)

        if queryset.exists():
            queryset.delete()

        return Response(
            {'detail': _("Berhasil dihapus.")},
            status=response_status.HTTP_204_NO_CONTENT)
