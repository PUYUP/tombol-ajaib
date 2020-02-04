from uuid import UUID

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import (
    ObjectDoesNotExist, ValidationError as _ValidationError)

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAcceptable, ValidationError, NotFound

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from ...utils.auths import validate_secure_code, mark_secure_code_used

Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')
SecureCode = get_model('person', 'SecureCode')


class ValidationSerializer(serializers.ModelSerializer):
    """ Serialize Validation, not user
    Only user as Person show """
    value = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(
        view_name='persons:validation-detail', lookup_field='uuid', read_only=True)

    class Meta:
        model = Validation
        exclude = ('id', 'roles', 'content_type',)

    def get_value(self, obj):
        field_type = obj.field_type
        request = self.context['request']
        person_pk = request.person_pk
        value_field = 'value_%s' % field_type
        value = getattr(obj, value_field, '')

        if field_type == 'image' or field_type == 'file':
            try:
                obj_file = obj.validationvalue_set.get(
                    object_id=person_pk, validation__identifier=obj.identifier)
            except ObjectDoesNotExist:
                obj_file = None

            # File exists
            if obj_file:
                file = getattr(obj_file, 'value_%s' % field_type, None)
                if file:
                    value = request.build_absolute_uri(file.url)

        value_dict = {
            'uuid': getattr(obj, 'value_uuid', None),
            'is_verified': getattr(obj, 'is_verified', None),
            'field': field_type,
            'print': value,
        }

        return value_dict

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        {
            "value": "12343",
            "secure_code": "KMC01CE1",
            "secure_hash": "dds"
        }
        """
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        identifier = instance.identifier
        field_type = instance.field_type
        method = instance.method
        is_secured = instance.is_secured
        is_unique = instance.is_unique
        value = request.data.get('value', None)
        secure_code = request.data.get('secure_code', None)
        secure_hash = request.data.get('secure_hash', None)
        person = request.person
        content_type = ContentType.objects.get_for_model(person)

        if person:
            data = {
                identifier: {'value_field': value}
            }

            # Value exist, so the action is verification
            # Make this value 'is_verified'
            if not secure_code or not secure_hash and is_secured:
                raise NotAcceptable(detail=_("Kode otentikasi salah."))

            if method == 'email':
                if not validate_secure_code(self, secure_code=secure_code,
                                            secure_hash=secure_hash):
                    raise NotAcceptable(detail=_("Kode otentikasi salah."))

            if method == 'sms':
                # Get secured code in database
                try:
                    secure_code_obj = SecureCode.objects.get(
                        identifier=identifier,
                        person=person,
                        is_used=False)
                except ObjectDoesNotExist:
                    raise NotAcceptable(detail=_("Kode otentikasi salah."))

                if secure_code != secure_code_obj.secure_code:
                    raise NotAcceptable(detail=_("Kode otentikasi salah."))

            # Set is_verified value to True
            data[identifier]['is_secure_code_valid'] = True

            # Secure code used
            mark_secure_code_used(
                self, secure_code=secure_code, person_pk=person.pk)

            try:
                queryset = Validation.objects.update_value(
                    identifier, value, request=request)
            except _ValidationError as e:
                errors = list(e.messages)
                raise ValidationError(detail=errors)

            return queryset
        return validated_data
