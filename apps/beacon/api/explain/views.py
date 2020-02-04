import json

from django.db import transaction
from django.db.models import (
    F, When, Case, OuterRef, Subquery, Prefetch, Count, Q, Value,
    CharField)
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib import messages

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable

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
        """ Can use 'guide_uuid' or 'chapter_uuid' """
        context = {'request': self.request}
        params = request.query_params
        person_pk = request.person_pk
        guide_uuid = params.get('guide_uuid', None)
        chapter_uuid = params.get('chapter_uuid', None)
        person_uuid = params.get('person_uuid', None)

        guide_uuid = check_uuid(uid=guide_uuid)
        chapter_uuid = check_uuid(uid=chapter_uuid)

        if not chapter_uuid and not guide_uuid:
            raise NotAcceptable(detail=_("UUID invalid."))

        # Person UUID defined
        if person_uuid:
            person_uuid = check_uuid(uid=person_uuid)

            if not person_uuid:
                raise NotAcceptable(detail=_("Person UUID invalid."))

        # ...
        # ExplainRevision objects in Subquery
        # ...
        revision_objs = ExplainRevision.objects.filter(explain_id=OuterRef('id'))
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

        queryset = Explain.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'),
                              Prefetch('chapter'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'chapter', 'guide') \
            .filter(
                Q(chapter__uuid=chapter_uuid) | Q(chapter__chapter_revisions__uuid=chapter_uuid)
                | Q(guide__uuid=guide_uuid) | Q(guide__guide_revisions__uuid=guide_uuid)) \
            .annotate(
                num_revision=Count('explain_revisions', distinct=True),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999
                ),
                **draft_fields,
                **published_fields) \
            .order_by('sort_stage', 'date_created') \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED))

        if person_uuid:
            queryset = queryset.filter(creator__uuid=person_uuid)

        if not queryset.exists():
            raise NotFound(_("Not found."))

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
            messages.add_message(request, messages.INFO, _("Materi berhasil dihapus."))

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
        person_pk = request.person_pk
        sortable = request.data.get('sortable', None)
        sortable_dict = json.loads(sortable)
        chapter_id = sortable_dict.get('chapter_id', None)
        sortable_list = sortable_dict.get('sorting', None)

        explain_list = list()
        explain_objs = Explain.objects.filter(
            id__in=sortable_list, creator_id=person_pk)

        if explain_objs.exists() and sortable_list:
            for index, item in enumerate(sortable_list, start=1):
                if item:
                    explain_obj = explain_objs.get(pk=item)
                    
                    setattr(explain_obj, 'stage', index)
                    setattr(explain_obj, 'chapter_id', chapter_id)
                    explain_list.append(explain_obj)

            Explain.objects.bulk_update(explain_list, ['stage', 'chapter_id'])
            return Response(status=response_status.HTTP_200_OK)
        raise NotFound()
