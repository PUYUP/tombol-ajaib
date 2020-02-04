from uuid import UUID

from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Case, When, Q, Prefetch, Exists
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError as _ValidationError
from django.core.files import File
from django.utils.html import strip_tags

# DRF
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError

# SERIALIZERS
from .serializers import AttributeSerializer, AttributeValueSerializer

# PERMISSIONS
from ..permissions import IsAllowCrudObject

# GET MODELS FROM GLOBAL UTILS
from utils.generals import get_model

# PERSON APP UTILS
from apps.person.utils.constant import FIELD_TYPE_CHOICES, OPTION, MULTI_OPTION

Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')


class AttributeApiView(viewsets.ViewSet):
    """ Get attribute options for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsAllowCrudObject],
        'destroy': [IsAllowCrudObject],
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
        identifiers = request.GET.get('identifiers', None)
        person_pk = request.person_pk

        # Attributes
        if person_pk and identifiers:
            identifiers = identifiers.split(',')
            queryset = Attribute.objects.attribute_values(
                identifiers=identifiers, request=request)

            # JSON Api
            serializer = AttributeSerializer(queryset, many=True, context=context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        raise NotAcceptable(detail=_("Data tidak valid."))

    # Update object validations
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None):
        """
        {
            "value": "Halo!"
        }
        """
        context = {'request': self.request}
        value = request.data.get('value', None)

        if not value:
            raise NotFound()

        try:
            uuid = UUID(uuid)
        except ValueError:
            raise NotFound()

        # Append file
        if request.FILES:
            setattr(request.data, 'files', request.FILES)

        queryset = Attribute.objects.get(uuid=uuid)
        serializer = AttributeSerializer(
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
        queryset = AttributeValue.objects.filter(uuid=uuid)
        if queryset.exists():
            queryset.delete()

        return Response(
            {'detail': _("Berhasil dihapus.")},
            status=response_status.HTTP_204_NO_CONTENT)

    # Update multiple attribute value
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['put'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='update', url_name='update_attributes')
    def update_attributes(self, request):
        context = {'request': self.request}
        identifiers = [key for key in request.data if key]

        queryset = Attribute.objects.update_values(
            identifiers=identifiers, request=request)

        serializer = AttributeSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
