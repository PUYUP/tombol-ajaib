from uuid import UUID
from itertools import chain

from django.db.models import Q, F, Subquery, OuterRef
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework.permissions import (
    AllowAny, IsAuthenticated)
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import ValidationSerializer

# PERMISSIONS
from ..permissions import IsAllowCrudObject

# GET MODELS FROM GLOBAL UTILS
from utils.generals import get_model

Validation = get_model('person', 'Validation')


class ValidationApiView(viewsets.ViewSet):
    """ Get validation for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsAllowCrudObject]
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

        # Validations
        if hasattr(request.user, 'person') and identifiers:
            person = getattr(request.user, 'person', None)
            identifiers = identifiers.split(',')

            # ContentType berdasarkan content (model)
            content_type = ContentType.objects.get_for_model(person)
            queryset = Validation.objects.get_validations(identifiers, person, content_type)

            # JSON Api
            serializer = ValidationSerializer(
                queryset, many=True, context=context)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        raise NotAcceptable(detail=_("Data tidak valid."))

    # Update object validations
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None):
        """
        {
            "value": "My value",
            "secure_code": "6A7704",
            "secure_hash": "Must-secured"
        }

        Note;
        'secure_code' and 'secure_hash' only used if update value
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

        try:
            queryset = Validation.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        serializer = ValidationSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
