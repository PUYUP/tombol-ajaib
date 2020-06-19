from django.db import transaction, IntegrityError
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import (
    ObjectDoesNotExist, ValidationError as _ValidationError)
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

# LOCAL UTILS
from apps.beacon.utils.discussion import get_enrollment_obj

EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')
EnrollmentChapter = get_model('beacon', 'EnrollmentChapter')
EnrollmentExplain= get_model('beacon', 'EnrollmentExplain')


class EnrollmentGuideSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = EnrollmentGuide
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        created = None

        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable(detail=_("Request not defined."))

        # Append request to objects
        setattr(EnrollmentGuide, 'request', request)

        try:
            obj, created = EnrollmentGuide.objects.get_or_create(**validated_data)
        except IntegrityError:
            raise NotAcceptable(detail=_("Integrity error."))

        if not created:
            raise NotAcceptable(detail=_("You has Enrolled this."))
        return obj
