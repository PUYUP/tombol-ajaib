from django.db import transaction
from django.db.models import (
    Q, F, Prefetch, Count, Case, When, OuterRef, Subquery)
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError

# SERIALIZERS
from .serializers import ChapterSerializer, ChapterCreateSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

Chapter = get_model('beacon', 'Chapter')
ChapterRevision = get_model('beacon', 'ChapterRevision')


class ChapterApiView(viewsets.ViewSet):
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
        params = request.query_params
        guide_uuid = params.get('guide_uuid', None)

        guide_uuid = check_uuid(uid=guide_uuid)
        if not guide_uuid:
            raise NotAcceptable(detail=_("Guide UUID invalid."))

        # ...
        # Annotate Published ChapterRevision
        # ...
        published_params = dict()
        published_fields = ('uuid', 'label', 'version', 'status', 'date_created')
        published_revisions = ChapterRevision.objects \
            .filter(chapter_id=OuterRef('id'), status=PUBLISHED)

        for item in published_fields:
            published_params['published_%s' % item] = Subquery(published_revisions.values(item)[:1])

        # ...
        # Annotate Draft ChapterRevision
        # ...
        draft_fields = ('uuid', 'label', 'version', 'status')
        draft_params = dict()
        draft_revisions = ChapterRevision.objects \
            .filter(chapter_id=OuterRef('id'), status=DRAFT) \
            .order_by('-version')

        for item in draft_fields:
            draft_params['draft_%s' % item] = Subquery(draft_revisions.values(item)[:1])

        queryset = Chapter.objects \
            .prefetch_related(Prefetch('creator'), Prefetch('creator__user'), Prefetch('guide')) \
            .select_related('creator', 'creator__user', 'guide') \
            .filter(Q(guide__uuid=guide_uuid) | Q(guide__guide_revisions__uuid=guide_uuid)) \
            .annotate(
                num_revision=Count('chapter_revisions', distinct=True),
                num_explain=Count('explains', distinct=True),
                sort_stage=Case(
                    When(stage__isnull=False, then=F('stage')),
                    default=99999),
                **published_params,
                **draft_params) \
            .order_by('sort_stage') \
            .exclude(~Q(creator_id=person_pk), ~Q(published_status=PUBLISHED))

        if not queryset.exists():
            raise NotFound(_("Not found."))

        serializer = ChapterSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = ChapterCreateSerializer(data=request.data, context=context)

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
        queryset = Chapter.objects.filter(uuid=uuid, creator=person)

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

        chapter_list = list()
        chapter_objs = Chapter.objects.filter(
            pk__in=sortable_list, creator=person)

        if chapter_objs.exists() and sortable_list:
            for index, item in enumerate(sortable_list, start=1):
                if item:
                    chapter_obj = chapter_objs.get(pk=item)
                    setattr(chapter_obj, 'stage', index)
                    chapter_list.append(chapter_obj)

            Chapter.objects.bulk_update(chapter_list, ['stage'])
            return Response(status=response_status.HTTP_200_OK)
        raise NotFound()
