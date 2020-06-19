from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

# DRF
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError

# SERIALIZERS
from .serializers import IntroductionSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# PROJECT UTILS
from utils.generals import get_model, check_uuid

Introduction = get_model('beacon', 'Introduction')


class IntroductionApiView(viewsets.ViewSet):
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
        serializer = IntroductionSerializer(data=request.data, context=context)

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
            queryset = Introduction.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        serializer = IntroductionSerializer(
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
        queryset = Introduction.objects.filter(uuid=uuid, creator=person)

        if queryset.exists():
            queryset.delete()

            return Response(
                {'detail': _("Berhasil dihapus.")},
                status=response_status.HTTP_204_NO_CONTENT)
        raise NotFound()
