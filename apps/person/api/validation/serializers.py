from uuid import UUID

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import (
    ObjectDoesNotExist, ValidationError as CoreValidationError)

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
        attr_type = obj.field_type
        request = self.context['request']
        person = getattr(request.user, 'person', None)
        name = 'value_%s' % attr_type
        value = getattr(obj, name, None)
        value_print = getattr(obj, 'label', None)

        if person:
            if attr_type == 'image' and hasattr(obj, 'value_image'):
                try:
                    obj_file = obj.validationvalue_set.get(
                        person=person, validation__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_image:
                    value = request.build_absolute_uri(
                        obj_file.value_image.url)

            if attr_type == 'file' and hasattr(obj, 'value_file'):
                try:
                    obj_file = obj.validationvalue_set.get(
                        person=person, validation__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_file:
                    value = request.build_absolute_uri(
                        obj_file.value_file.url)

            value_dict = {
                'uuid': getattr(obj, 'value_uuid', None),
                'field': name,
                'object': value,
                'object_print': value_print,
                'is_verified': getattr(obj, 'is_verified', None),
            }
            return value_dict
        return None

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
        person = getattr(request.user, 'person', None)
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

            # Check duplicate
            if is_unique:
                validation_value = ValidationValue.objects \
                    .filter(
                        validation__identifier=identifier,
                        is_verified=True,
                        **{'value_%s__iexact' % field_type: value}) \
                    .exclude(object_id=person.pk)

                if validation_value.exists():
                    raise NotAcceptable(
                        detail=_("%s sudah digunakan, coba yang lain." % instance.label))

            try:
                Validation.objects.update_value(
                    data, person, content_type)
            except CoreValidationError as e:
                errors = list(e.messages)
                raise ValidationError(errors)

            return Validation.objects \
                .get_validation(identifier, person, content_type)
        return validated_data
