import asyncio
from datetime import date, datetime

from django.db import models, IntegrityError
from django.db.models import Q, F, Case, When, Value, CharField, Subquery, Exists, OuterRef
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import RegexValidator, validate_email, URLValidator
from django.core.files import File

from pprint import pprint

# PROJECT UTILS
from utils.generals import get_model

loop = asyncio.get_event_loop()

def upload_file(file_data):
    instance = file_data.get('instance', None)
    value = file_data.get('value', None)
    field_type = file_data.get('field_type', None)
    filename = getattr(value, 'name', None)

    if field_type == 'image':
        instance.value_image.save(filename, value, save=True)

    if field_type == 'file':
        instance.value_file.save(filename, value, save=True)


class ValidationManager(models.Manager):
    """===========================================================
    Start validators
    ==========================================================="""
    def validate_value(self, field_type, value):
        validator = getattr(self, '_validate_%s' % field_type)
        validator(value)

    def validate_required(self, field_type, value):
        if not value:
            raise ValidationError(_("Value is required"))

    def _validate_text(self, value):
        if not isinstance(value, str):
            raise ValidationError(_("Must be str"))
    _validate_richtext = _validate_text

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a file."))

    def _validate_image(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a image."))

    def _validate_email(self, value):
        if value:
            validate_email(value)

    def _validate_url(self, value):
        if value:
            try:
                validate = URLValidator(schemes=('http', 'https'))
                validate(value)
            except ValidationError:
                raise ValidationError(_("Enter a valid URL."))

    """===========================================================
    Validations called here
    ==========================================================="""
    def get_validation(self, identifier, person, content_type):
        if not identifier or not person or not content_type:
            return None

        queryset = self.prefetch_related('content_type') \
            .filter(
                content_type=content_type,
                identifier=identifier,
                validationvalue__object_id=person.pk) \
            .distinct()
        
        if not queryset.exists():
            return None

        # Extract validation value
        ValidationValue = get_model('person', 'ValidationValue')
        validation_values = ValidationValue.objects \
            .prefetch_related('validation',  'content_type') \
            .select_related('validation',  'content_type') \
            .filter(
                validation__identifier__in=OuterRef('identifier'),
                object_id=person.pk)

        annotate = dict()
        for q in queryset:
            value_field = 'value_' + q.field_type
            annotate[value_field] = Subquery(validation_values.values(value_field)[:1])
            annotate['value_uuid'] = Subquery(validation_values.values('uuid')[:1])
            annotate['is_verified'] = Subquery(validation_values.values('is_verified')[:1])

        # Call value each field
        return queryset.annotate(**annotate).first()

    def get_validations(self, identifiers, person, content_type=None):
        if (not identifiers and type(identifiers) != list()) or not person:
            return None

        roles = person.roles.filter(is_active=True) \
            .values_list('id', flat=True)

        queryset = self.prefetch_related('content_type', 'roles') \
            .filter(
                content_type=content_type,
                identifier__in=identifiers,
                roles__in=roles) \
            .distinct()

        if not queryset.exists():
            return None

        # Extract validation value
        ValidationValue = get_model('person', 'ValidationValue')
        validation_values = ValidationValue.objects \
            .prefetch_related('validation',  'content_type') \
            .select_related('validation',  'content_type') \
            .filter(
                validation__identifier__in=OuterRef('identifier'),
                object_id=person.pk)

        annotate = dict()
        for q in queryset:
            value_field = 'value_' + q.field_type
            annotate[value_field] = Subquery(validation_values.values(value_field)[:1])
            annotate['value_uuid'] = Subquery(validation_values.values('uuid')[:1])
            annotate['is_verified'] = Subquery(validation_values.values('is_verified')[:1])
        return queryset.annotate(**annotate)

    def check_validations(self, person, content_type=None):
        roles = person.roles.filter(is_active=True) \
            .values_list('id', flat=True)

        queryset = self.prefetch_related('content_type', 'roles') \
            .filter(
                content_type=content_type,
                is_required=True,
                roles__in=roles) \
            .distinct()

        if not queryset.exists():
            return None

        # Extract validation value
        ValidationValue = get_model('person', 'ValidationValue')
        validation_values = ValidationValue.objects \
            .prefetch_related('validation',  'content_type') \
            .select_related('validation',  'content_type') \
            .filter(
                validation__identifier__in=OuterRef('identifier'),
                object_id=person.pk,
                is_verified=True)

        annotate = dict()
        for q in queryset:
            value_field = 'value_' + q.field_type
            annotate['is_verified'] = Exists(validation_values)
            annotate[value_field] = Exists(validation_values)
        return queryset.annotate(**annotate)

    """===========================================================
    Validations set or update here
    ==========================================================="""
    def set_value(self, params, person, content_type):
        """Params:
        {
            'identifier': 'value',
        }

        Bulk create need parameter;
        validation, value, content_type and object_id
        """
        if not params or not person or not content_type:
            return False

        ValidationValue = get_model('person', 'ValidationValue')

        roles = person.roles.filter(is_active=True).prefetch_related('person') \
            .values_list('id', flat=True)
        roles_q = Q(roles__in=roles)

        keys_q = Q()
        param_keys = [key for key in params if key]
        if param_keys:
            keys_q = Q(identifier__in=param_keys)

        # Grab the current validation value
        value_objects = person.validation_values \
            .prefetch_related('validation', 'content_type') \
            .select_related('validation', 'content_type') \
            .filter(Q(content_type=content_type)) \
            .values('validation__identifier')

        # Exlude validation not assigned to create new value
        value_params = list()
        queryset = self.prefetch_related('content_type', 'roles') \
            .filter(roles_q, keys_q, Q(content_type=content_type)) \
            .exclude(identifier__in=value_objects) \
            .distinct()

        if queryset.exists():
            for item in queryset:
                identifier = item.identifier
                field_type = item.field_type
                is_required = item.is_required
                value_field = 'value_%s' % field_type

                # Grab value
                try:
                    value = params[identifier]['value_field']
                except KeyError:
                    value = None

                # Set all parameter
                value_object = ValidationValue(
                    validation=item,
                    content_type=content_type,
                    object_id=person.id)

                # Value is File or Image
                if isinstance(value, File):
                    file_data = {
                        'field_type': field_type,
                        'instance': value_object,
                        'value': value
                    }
                    loop.run_in_executor(None, upload_file, file_data)

                else:
                    setattr(value_object, value_field, value)

                # Validate
                self.validate_value(field_type, value)

                if is_required:
                    self.validate_required(field_type, value)

                # Collect validation value object
                value_params.append(value_object)

            # And final create all
            if value_params:
                return ValidationValue.objects \
                    .bulk_create(value_params, ignore_conflicts=True)
            return False
        return False

    def update_value(self, params, person, content_type):
        """All params like 'set_value' above"""
        if not params or not person or not content_type:
            return False

        roles = person.roles.filter(is_active=True) \
            .values_list('id', flat=True)
        roles_q = Q(validation__roles__in=roles)

        keys_q = Q()
        param_keys = [key for key in params if key]
        if param_keys:
            keys_q = Q(validation__identifier__in=param_keys)

        # Get all validation values from this entity (ex: person)
        # But limitation by roles and keys (identifiers)
        values_queryset = person.validation_values
        queryset = values_queryset.prefetch_related('validation', 'content_type') \
            .select_related('validation', 'content_type') \
            .filter(roles_q, keys_q, Q(content_type=content_type)) \
            .distinct()

        # Create!
        self.set_value(params, person, content_type)

        # Update!
        if queryset.exists():
            ValidationValue = getattr(values_queryset, 'model', None)

            if not ValidationValue:
                return False

            value_fields = list()
            value_object_list = list()

            for item in queryset:
                identifier = item.validation.identifier
                field_type = item.validation.field_type
                is_required = item.validation.is_required
                value_field = 'value_%s' % field_type

                # Get validation_value object
                value_object = queryset.get(
                    validation__identifier=identifier,
                    content_type=content_type,
                    object_id=person.pk)

                # Grab value
                try:
                    param = params[identifier]
                except KeyError:
                    param = None
  
                value = param.get('value_field', None)
                is_secure_code_valid = param.get('is_secure_code_valid', None)

                if isinstance(value, File):
                    file_data = {
                        'field_type': field_type,
                        'instance': value_object,
                        'value': value
                    }
                    loop.run_in_executor(None, upload_file, file_data)

                else:
                    setattr(value_object, value_field, value)

                    # Change is_verified value to True
                    if is_secure_code_valid:
                        setattr(value_object, 'is_verified', True)
                        value_fields.append('is_verified')

                    # Collect field value, ex: 'value_text'
                    value_fields.append(value_field)

                # Validate
                self.validate_value(field_type, value)

                if is_required:
                    self.validate_required(field_type, value)

                # Make a list from validation value object
                value_object_list.append(value_object)

            # If update success return 'None'
            if value_object_list:
                return ValidationValue.objects.bulk_update(
                    value_object_list, value_fields)
            return None
        return False
