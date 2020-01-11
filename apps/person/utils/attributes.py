import asyncio
from datetime import date, datetime

from django.db import models, IntegrityError
from django.db.models import Q, F, Subquery, OuterRef
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import RegexValidator, validate_email, URLValidator
from django.core.files import File

from pprint import pprint

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from ..utils.constant import (
    OPTION,
    MULTI_OPTION)

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


class AttributeManager(models.Manager):
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

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_("Must be a float"))

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError(_("Must be a datetime"))

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_multi_option(self, value):
        try:
            values = iter(value)
        except TypeError:
            raise ValidationError(
                _("Must be a list or AttributeOption queryset"))

        # Validate each value as if it were an option
        # Pass in valid_values so that the DB
        # isn't hit multiple times per iteration
        if values:
            AttributeOption = get_model('person', 'AttributeOption')
            valid_values = AttributeOption.objects.filter(pk__in=values)
            for item in valid_values:
                self._validate_option(item, valid_values=valid_values)

    def _validate_option(self, value, valid_values=None):
        if not isinstance(value, get_model('person', 'AttributeOption')):
            raise ValidationError(
                _("Must be an AttributeOption model object instance"))

        if not value.pk:
            raise ValidationError(_("AttributeOption has not been saved yet"))

        if valid_values is None:
            AttributeOption = get_model('person', 'AttributeOption')
            valid_values = AttributeOption.objects.filter(pk__in=[value.pk])

        if value not in valid_values:
            raise ValidationError(
                _("%(enum)s is not a valid choice for %(attr)s") %
                {'enum': value, 'attr': self})

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
    Attributes called here
    ==========================================================="""
    def get_attribute(self, identifier, person, content_type):
        if not identifier or not person or not content_type:
            return None

        queryset = self.prefetch_related('option_group', 'content_type') \
            .select_related('option_group') \
            .filter(
                content_type=content_type,
                identifier=identifier,
                attributevalue__object_id=person.pk) \
            .distinct()
        
        if not queryset.exists():
            return None

        # Extract attribute value
        AttributeValue = get_model('person', 'AttributeValue')
        attribute_values = AttributeValue.objects \
            .prefetch_related('attribute',  'content_type') \
            .select_related('attribute',  'content_type') \
            .filter(
                attribute__identifier__in=OuterRef('identifier'),
                object_id=person.pk)

        annotate = dict()
        for q in queryset:
            value_field = 'value_' + q.field_type
            annotate[value_field] = Subquery(attribute_values.values(value_field)[:1])
            annotate['value_uuid'] = Subquery(attribute_values.values('uuid')[:1])

        # Call value each field
        return queryset.annotate(**annotate).first()

    def get_attributes(self, identifiers, person, content_type=None):
        if (not identifiers and type(identifiers) != list()) or not person:
            return None

        roles = person.roles.filter(is_active=True) \
            .values_list('id', flat=True)

        queryset = self.prefetch_related('option_group', 'content_type', 'roles') \
            .select_related('option_group') \
            .filter(
                content_type=content_type,
                identifier__in=identifiers,
                roles__in=roles) \
            .distinct()

        if not queryset.exists():
            return None

        # Extract attribute value
        AttributeValue = get_model('person', 'AttributeValue')
        attribute_values = AttributeValue.objects \
            .prefetch_related('attribute',  'content_type') \
            .select_related('attribute',  'content_type') \
            .filter(
                attribute__identifier__in=OuterRef('identifier'),
                object_id=person.pk)

        annotate = dict()
        for q in queryset:
            value_field = 'value_' + q.field_type
            annotate[value_field] = Subquery(attribute_values.values(value_field)[:1])
            annotate['value_uuid'] = Subquery(attribute_values.values('uuid')[:1])
        return queryset.annotate(**annotate)

    """===========================================================
    Attributes set or update here
    ==========================================================="""
    def set_value(self, params, person, content_type):
        """Params:
        {
            'identifier': 'value',
        }

        Bulk create need parameter;
        attribute, value, content_type and object_id
        """
        if not params or not person or not content_type:
            return False

        AttributeValue = get_model('person', 'AttributeValue')

        roles = person.roles.filter(is_active=True).prefetch_related('person') \
            .values_list('id', flat=True)
        roles_q = Q(roles__in=roles)

        keys_q = Q()
        param_keys = [key for key in params if key]
        if param_keys:
            keys_q = Q(identifier__in=param_keys)

        # Grab the current attribute value
        value_objects = person.attribute_values \
            .prefetch_related('attribute', 'content_type', 'value_option') \
            .select_related('attribute', 'content_type', 'value_option') \
            .filter(Q(content_type=content_type)) \
            .values('attribute__identifier')

        # Exlude attribute not assigned to create new value
        value_params = list()
        queryset = self.prefetch_related('option_group', 'content_type', 'roles') \
            .select_related('option_group') \
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
                    value = params[identifier]
                except KeyError:
                    value = None

                # Set all parameter
                value_object = AttributeValue(
                    attribute=item,
                    content_type=content_type,
                    object_id=person.id)

                # Value is option
                if field_type == OPTION:
                    pass

                # Value is multi option (multi checkbox)
                elif field_type == MULTI_OPTION:
                    pass

                # Value is File or Image
                elif isinstance(value, File):
                    file_data = {
                        'field_type': field_type,
                        'instance': value_object,
                        'value': value
                    }
                    loop.run_in_executor(None, upload_file, file_data)

                else:
                    setattr(value_object, value_field, value)

                # Validate
                if field_type != OPTION and field_type != MULTI_OPTION:
                    self.validate_value(field_type, value)

                    if is_required:
                        self.validate_required(field_type, value)

                # Collect attribute value object
                value_params.append(value_object)

            # And final create all
            if value_params:
                return AttributeValue.objects \
                    .bulk_create(value_params, ignore_conflicts=True)
            return False
        return False

    def update_value(self, params, person, content_type):
        """All params like 'set_value' above"""
        if not params or not person or not content_type:
            return False

        roles = person.roles.filter(is_active=True) \
            .values_list('id', flat=True)
        roles_q = Q(attribute__roles__in=roles)

        keys_q = Q()
        param_keys = [key for key in params if key]
        if param_keys:
            keys_q = Q(attribute__identifier__in=param_keys)

        # Get all attribute values from this entity (ex: person)
        # But limitation by roles and keys (identifiers)
        values_queryset = person.attribute_values
        queryset = values_queryset.prefetch_related('attribute', 'content_type', 'value_option') \
            .select_related('attribute', 'content_type', 'value_option') \
            .filter(roles_q, keys_q, Q(content_type=content_type)) \
            .distinct()

        # Create!
        self.set_value(params, person, content_type)

        # Update!
        if queryset.exists():
            AttributeValue = getattr(values_queryset, 'model', None)

            if not AttributeValue:
                return False

            value_fields = list()
            value_object_list = list()

            for item in queryset:
                identifier = item.attribute.identifier
                field_type = item.attribute.field_type
                is_required = item.attribute.is_required
                value_field = 'value_%s' % field_type

                # Get attribute_value object
                value_object = queryset.get(
                    attribute__identifier=identifier,
                    content_type=content_type,
                    object_id=person.pk)

                # Grab value
                try:
                    value = params[identifier]
                except KeyError:
                    value = None

                # Value is option
                if field_type == OPTION:
                    try:
                        value = int(value)
                    except ValueError:
                        raise ValidationError(_("Must be an integer"))

                    try:
                        value = value_object.attribute \
                            .option_group.options.get(id=value)
                    except ObjectDoesNotExist:
                        value = None

                    setattr(value_object, value_field, value)
                    value_object.save()

                # Value is multi option (multi checkbox)
                elif field_type == MULTI_OPTION:
                    # Multi option
                    value_list = list()
                    for val in value:
                        if val:
                            try:
                                val = int(val)
                                value_list.append(val)
                            except ValueError:
                                pass

                    if value:
                        getattr(value_object, value_field).set(filter(None, value_list))

                # Value is File or Image
                elif isinstance(value, File):
                    file_data = {
                        'field_type': field_type,
                        'instance': value_object,
                        'value': value
                    }
                    loop.run_in_executor(None, upload_file, file_data)

                else:
                    setattr(value_object, value_field, value)

                    # Collect field value, ex: 'value_text'
                    value_fields.append(value_field)

                # Validate
                self.validate_value(field_type, value)

                if is_required:
                    self.validate_required(field_type, value)

                # Make a list from attribute value object
                value_object_list.append(value_object)

            # If update success return 'None'
            # We modify, so far return 'True'
            if value_object_list and value_fields:
                return AttributeValue.objects.bulk_update(
                    value_object_list, value_fields)
            return False
        return False
