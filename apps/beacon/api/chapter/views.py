from django.db import transaction
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
from .serializers import ChapterSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# # PROJECT UTILS
from utils.generals import get_model, check_uuid

Chapter = get_model('beacon', 'Chapter')


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

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = ChapterSerializer(data=request.data, context=context)

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

        person = getattr(request.user, 'person', None)
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
        person = getattr(request.user, 'person', None)
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
