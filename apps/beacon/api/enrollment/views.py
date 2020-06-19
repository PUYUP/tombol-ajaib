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

from pprint import pprint

# SERIALIZERS
from .serializers import EnrollmentGuideSerializer

# PERMISSIONS
from apps.beacon.utils.permissions import IsAllowCrudObject

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.discussion import get_enrollment_obj
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')
EnrollmentChapter = get_model('beacon', 'EnrollmentChapter')
EnrollmentExplain= get_model('beacon', 'EnrollmentExplain')


class EnrollmentGuideApiView(viewsets.ViewSet):
    """ Get attribute options for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (AllowAny, IsAuthenticated,)
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
        serializer = EnrollmentGuideSerializer(data=request.data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
