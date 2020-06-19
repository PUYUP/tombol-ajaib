from django.db import transaction
from django.db.models import (
    Count, OuterRef, Subquery, Case, When, Prefetch, Q, F)
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (
    ObjectDoesNotExist, ValidationError as _ValidationError)

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError
from rest_framework.pagination import PageNumberPagination

from pprint import pprint

# SERIALIZERS
from .serializers import TopicSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.discussion import get_enrollment_obj
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Topic = get_model('beacon', 'Topic')
TopicRevision = get_model('beacon', 'TopicRevision')
EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')
EnrollmentChapter = get_model('beacon', 'EnrollmentChapter')
EnrollmentExplain= get_model('beacon', 'EnrollmentExplain')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


class TopicApiView(viewsets.ViewSet):
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

    def get_object(self, request, uuid=None, extend_fields=list()):
        person_pk = request.person_pk
        params = request.query_params

        # Get enrollment object
        # One of Guide, Chapter or Explain
        enrollment_obj = None
        enrollment_uuid = params.get('enrollment_uuid', None)
        enrollment_type = params.get('enrollment_type', None)

        try:
            enrollment_obj = get_enrollment_obj(etype=enrollment_type, uuid=enrollment_uuid)
        except _ValidationError as e:
            raise NotAcceptable(' '.join(e))

        model_name = enrollment_obj._meta.model_name
        content_type = ContentType.objects.get(app_label='beacon', model=model_name)

        # ...
        # TopicRevision objects in Subquery
        # ...
        revision_objs = TopicRevision.objects.filter(topic_id=OuterRef('id'))
        revision_fields = ['uuid', 'label', 'version', 'status', 'date_created']

        # More fields?
        if len(extend_fields) > 0:
            revision_fields = revision_fields + extend_fields

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
        queryset = Topic.objects \
            .prefetch_related(Prefetch('content_object'), Prefetch('content_type'), Prefetch('creator')) \
            .select_related('content_type', 'creator') \
            .filter(content_type=content_type, object_id=enrollment_obj.id) \
            .annotate(
                num_revision=Count('topic_revisions', distinct=True),
                **draft_fields,
                **published_fields) \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED))

        # ...
        # Single object
        # ...
        if uuid:
            try:
                queryset = queryset.filter(uuid=uuid).get()
            except ObjectDoesNotExist:
                raise NotFound()
        return queryset

    def list(self, request, format=None):
        """
        enrollment_type: one of topic, chapter or explain
        """
        context = {'request': self.request}
        params = request.query_params
        person_uuid = params.get('person_uuid', None)

        # Person UUID defined
        if person_uuid:
            person_uuid = check_uuid(uid=person_uuid)
            if not person_uuid:
                raise NotAcceptable(detail=_("Person UUID invalid."))

        # Get objects...
        queryset = self.get_object(request)

        if person_uuid:
            queryset = queryset.filter(creator__uuid=person_uuid)

        if not queryset.exists():
            raise NotFound()

        queryset_paginate = PAGINATOR.paginate_queryset(queryset, request)
        serializer = TopicSerializer(queryset_paginate, many=True, context=context)

        response = {
            'count': PAGINATOR.page.paginator.count,
            'navigate': {
                'previous': PAGINATOR.get_previous_link(),
                'next': PAGINATOR.get_next_link()
            },
            'results': serializer.data
        }

        return Response(response, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = TopicSerializer(data=request.data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update object validations
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None):
        context = {'request': self.request}

        uuid = check_uuid(uid=uuid)
        if not uuid:
            raise NotFound()

        try:
            queryset = Topic.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        serializer = TopicSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
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
        queryset = Topic.objects.filter(uuid=uuid, creator=person)

        if queryset.exists():
            queryset.delete()

            return Response(
                {'detail': _("Berhasil dihapus.")},
                status=response_status.HTTP_204_NO_CONTENT)
        raise NotFound()
