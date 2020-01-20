from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, Prefetch)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
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
        person_pk = request.person_pk

        # ...
        # Get last ExplainRevision
        # ...
        explain_params = dict()
        explain_fields = ('uuid', 'date_created')
        explain_revisions = ExplainRevision.objects \
            .filter(explain__guide__pk=OuterRef('pk')) \
            .order_by('-date_updated')

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_explain=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Get last ChapterRevision
        # ...
        chapter_params = dict()
        chapter_fields = ('uuid', 'date_created')
        chapter_revisions = ChapterRevision.objects \
            .filter(chapter__guide__pk=OuterRef('pk')) \
            .order_by('-date_updated')

        for item in chapter_fields:
            chapter_params['chapter_%s' % item] = Case(
                When(num_chapter=1, then=Subquery(chapter_revisions.values(item)[:1])),
                default=Subquery(chapter_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Get last GuideRevision
        # ...
        revision_fields = ('uuid', 'label', 'version')
        revision_params = dict()
        revisions = GuideRevision.objects.filter(guide__pk=OuterRef('pk'))

        for item in revision_fields:
            revision_params['revision_%s' % item] = Case(
                When(num_revision=1, then=Subquery(revisions.values(item)[:1])),
                default=Subquery(revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        # ...
        # Upcoming GuideRevision
        # Get last DRAFT
        # ...
        upcoming_fields = ('uuid', 'label', 'version')
        upcoming_params = dict()
        upcomings = GuideRevision.objects \
            .filter(guide__pk=OuterRef('pk')) \
            .order_by('-version')

        for item in upcoming_fields:
            upcoming_params['upcoming_%s' % item] = Case(
                When(num_revision=1, then=Subquery(upcomings.values(item)[:1])),
                default=Subquery(upcomings.filter(status=DRAFT).values(item)[:1])
            )

        # ...
        # Run query
        # ...
        queryset = Guide.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user')) \
            .select_related('creator', 'creator__user') \
            .filter(creator__pk=person_pk) \
            .annotate(
                num_revision=Count('guide_revisions', distinct=True),
                num_explain=Count('explains', distinct=True),
                num_chapter=Count('chapters', distinct=True),
                **revision_params,
                **upcoming_params,
                **chapter_params,
                **explain_params)

        queryset_paginate = PAGINATOR.paginate_queryset(queryset, request)
        serializer = GuideListSerializer(queryset_paginate, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

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
