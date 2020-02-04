import asyncio

from django.db import models
from django.db.models import Subquery, Exists, OuterRef, Prefetch
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import RegexValidator, validate_email, URLValidator
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from ..utils.constant import FIELD_VALIDATION_CHOICES

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
    # ...
    # Get validation values
    # ...
    def validation_values(self, *agrs, **kwargs):
        value_params = dict()
        request = kwargs.get('request', None)
        identifiers = kwargs.get('identifiers', list())
        content_type = ContentType.objects.get(app_label='person', model='person')
        validationvalue_model = self.model.validationvalue_set.field.model
        person_pk = request.person_pk

        role_objs = request.person.roles.filter(is_active=True).prefetch_related('person') \
            .values_list('id', flat=True)

        validation_value_objs = validationvalue_model.objects \
            .prefetch_related(Prefetch('validation'), Prefetch('content_type')) \
            .select_related('validation', 'content_type') \
            .filter(
                validation_id=OuterRef('id'),
                content_type=content_type.id,
                object_id=person_pk)

        for item in FIELD_VALIDATION_CHOICES:
            field_type = item[0]
            field_value = 'value_%s' % field_type
            value_params[field_value] = Subquery(validation_value_objs.values(field_value)[:1])

        value_params['value_uuid'] = Subquery(validation_value_objs.values('uuid')[:1])
        value_params['is_verified'] = Subquery(validation_value_objs.values('is_verified')[:1])

        queryset = self.model.objects \
            .filter(content_type=content_type.id, identifier__in=identifiers, roles__in=role_objs) \
            .annotate(**value_params)
        return queryset

    # ...
    # Update validation values
    # ...
    def update_values(self, *agrs, **kwargs):
        request = kwargs.get('request', None)
        identifiers = kwargs.get('identifiers', list())
        person_pk = request.person_pk
        content_type = ContentType.objects.get(app_label='person', model='person')
        validationvalue_model = self.model.validationvalue_set.field.model
        value_params = dict()
        fields_attr_target = list()
        create_attr_values = list()
        update_attr_values = list()

        role_objs = request.person.roles.filter(is_active=True).prefetch_related('person') \
            .values_list('id', flat=True)

        validation_value_objs = validationvalue_model.objects \
            .prefetch_related(Prefetch('validation'), Prefetch('content_type')) \
            .select_related('validation', 'content_type') \
            .filter(
                validation_id=OuterRef('id'),
                content_type=content_type.id,
                object_id=person_pk)

        for item in FIELD_VALIDATION_CHOICES:
            field_type = item[0]
            field_value = 'value_%s' % field_type
            value_params[field_value] = Exists(validation_value_objs)
            value_params['value_id'] = Subquery(validation_value_objs.values('id')[:1])

        queryset = self.model.objects \
            .filter(content_type=content_type.id, identifier__in=identifiers, roles__in=role_objs) \
            .annotate(**value_params)

        for item in queryset:
            is_unique = item.is_unique
            identifier = item.identifier
            field_type = item.field_type
            field_value = 'value_%s' % field_type
            value = request.data.get(identifier, None)
            is_exist = getattr(item, field_value, False)

            value_obj = validationvalue_model(
                validation_id=item.id,
                content_type=content_type,
                object_id=person_pk)

            # On update object need Target field to updated
            if is_exist:
                setattr(value_obj, 'id', item.value_id)

            if isinstance(value, File):
                file_data = {
                    'field_type': field_type,
                    'instance': value_obj,
                    'value': value
                }
                loop.run_in_executor(None, upload_file, file_data)

            else:
                value = strip_tags(value)

                # Check unique
                if is_unique:
                    duplicate_objs = validationvalue_model.objects \
                        .filter(
                            content_type=content_type,
                            validation__identifier=identifier,
                            is_verified=True,
                            **{'value_%s__iexact' % field_type: value}) \
                        .exclude(object_id=person_pk)

                    if duplicate_objs.exists():
                        raise ValidationError(_("%s sudah digunakan, coba yang lain." % item.label))

                setattr(value_obj, field_value, value)
                setattr(value_obj, 'is_verified', True)

                # Create or Update a value object
                if is_exist:
                    # On update object need Target field to updated
                    fields_attr_target.append(field_value)
                    update_attr_values.append(value_obj)
                else:
                    create_attr_values.append(value_obj)

        # Create
        if create_attr_values:
            validationvalue_model.objects.bulk_create(create_attr_values, ignore_conflicts=True)

        # Update
        if update_attr_values:
            validationvalue_model.objects.bulk_update(update_attr_values, fields_attr_target)

        # JSON Api
        queryset = self.validation_values(identifiers=identifiers, request=request)
        return queryset

    def update_value(self, identifier, value, *args, **kwargs):
        """ Return a single object, so use '.get()' """
        request = kwargs.get('request', None)
        request.data[identifier] = value
        queryset = self.update_values(identifiers=[identifier], request=request)

        # Update person is_validated if all validation passed
        is_passed = self.is_passed(request=request)
        if is_passed:
            person = getattr(request.user, 'person', None)
            if person:
                person.is_validated = True
                person.save()

        return queryset.get()

    # ...
    # Check validation is passed All
    # Only for required field
    # ...
    def is_passed(self, *args, **kwargs):
        valids = list()
        request = kwargs.get('request', None)
        person_pk = request.person_pk
        content_type = ContentType.objects.get(app_label='person', model='person')
        validationvalue_model = self.model.validationvalue_set.field.model

        validation_value_objs = validationvalue_model.objects \
            .filter(
                validation_id=OuterRef('id'),
                content_type=content_type.id,
                object_id=person_pk)

        validation_objs = self.model.objects \
            .filter(is_required=True) \
            .annotate(is_verified=Subquery(validation_value_objs.values('is_verified')[:1]))

        if not validation_objs.exists():
            return True

        for item in validation_objs:
            valids.append(item.is_verified)
        return None not in valids and False not in valids and '' not in valids
