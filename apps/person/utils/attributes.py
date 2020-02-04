import asyncio
from datetime import date, datetime
from pprint import pprint

from django.db import models
from django.db.models import Subquery, OuterRef, Prefetch, Exists
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from ..utils.constant import (
    OPTION,
    MULTI_OPTION,
    FIELD_TYPE_CHOICES)

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
    # ...
    # Get attributes with values
    # ...
    def attribute_values(self, *agrs, **kwargs):
        value_params = dict()
        request = kwargs.get('request', None)
        identifiers = kwargs.get('identifiers', list())
        content_type = ContentType.objects.get(app_label='person', model='person')
        attributevalue_model = self.model.attributevalue_set.field.model
        person_pk = request.person_pk

        role_objs = request.person.roles.filter(is_active=True).prefetch_related('person') \
            .values_list('id', flat=True)

        attribute_value_objs = attributevalue_model.objects \
            .prefetch_related(Prefetch('attribute'), Prefetch('content_type')) \
            .select_related('attribute', 'content_type') \
            .filter(
                attribute_id=OuterRef('id'),
                content_type=content_type.id,
                object_id=person_pk)

        for item in FIELD_TYPE_CHOICES:
            field_type = item[0]
            field_value = 'value_%s' % field_type
            value_params[field_value] = Subquery(attribute_value_objs.values(field_value)[:1])
        value_params['value_uuid'] = Subquery(attribute_value_objs.values('uuid')[:1])

        queryset = self.model.objects \
            .filter(content_type=content_type.id, identifier__in=identifiers, roles__in=role_objs) \
            .annotate(**value_params)
        return queryset

    # ...
    # Single value
    # ...
    def attribute_value(self, identifier, *args, **kwargs):
        request = kwargs.get('request', None)
        identifiers = [identifier]

        try:
            value_obj = self.attribute_values(
                identifiers=identifiers, request=request).get()
        except ObjectDoesNotExist:
            value_obj = None
        return value_obj

    # ...
    # Update attribute values
    # ...
    def update_values(self, *agrs, **kwargs):
        request = kwargs.get('request', None)
        identifiers = kwargs.get('identifiers', list())
        person_pk = request.person_pk
        content_type = ContentType.objects.get(app_label='person', model='person')
        attributevalue_model = self.model.attributevalue_set.field.model
        value_params = dict()
        fields_attr_target = list()
        create_attr_values = list()
        update_attr_values = list()

        role_objs = request.person.roles.filter(is_active=True).prefetch_related('person') \
            .values_list('id', flat=True)

        attribute_value_objs = attributevalue_model.objects \
            .prefetch_related(Prefetch('attribute'), Prefetch('content_type')) \
            .select_related('attribute', 'content_type') \
            .filter(
                attribute_id=OuterRef('id'),
                content_type=content_type.id,
                object_id=person_pk)

        for item in FIELD_TYPE_CHOICES:
            field_type = item[0]
            field_value = 'value_%s' % field_type
            value_params[field_value] = Exists(attribute_value_objs)
            value_params['value_id'] = Subquery(attribute_value_objs.values('id')[:1])

        # Append file
        if request.FILES:
            setattr(request.data, 'files', request.FILES)

        queryset = self.model.objects \
            .filter(content_type=content_type.id, identifier__in=identifiers, roles__in=role_objs) \
            .annotate(**value_params)

        for item in queryset:
            identifier = item.identifier
            field_type = item.field_type
            field_value = 'value_%s' % field_type
            value = request.data.get(identifier, None)
            is_exist = getattr(item, field_value, False)

            value_obj = attributevalue_model(
                attribute_id=item.id,
                content_type=content_type,
                object_id=person_pk)

            # On update object need Target field to updated
            if is_exist:
                setattr(value_obj, 'id', item.value_id)

            if field_type == OPTION:
                try:
                    value = value_obj.attribute \
                        .option_group.options.get(id__iexact=value)
                except ObjectDoesNotExist:
                    value = None

                setattr(value_obj, field_value, value)
                value_obj.save()

            elif field_type == MULTI_OPTION:
                value_list = list()
                if value:
                    value_list = value.split(',')

                # Creat the first object
                if not is_exist:
                    value_obj.save()

                # Then save it!
                value = value_list
                getattr(value_obj, field_value).set(filter(None, value_list))

            elif isinstance(value, File):
                file_data = {
                    'field_type': field_type,
                    'instance': value_obj,
                    'value': value
                }
                loop.run_in_executor(None, upload_file, file_data)

            else:
                value = strip_tags(value)
                setattr(value_obj, field_value, value)

                # Create or Update a value object
                if is_exist:
                    # On update object need Target field to updated
                    fields_attr_target.append(field_value)
                    update_attr_values.append(value_obj)
                else:
                    create_attr_values.append(value_obj)

        # Create
        if create_attr_values:
            attributevalue_model.objects.bulk_create(create_attr_values, ignore_conflicts=True)

        # Update
        if update_attr_values:
            attributevalue_model.objects.bulk_update(update_attr_values, fields_attr_target)

        # JSON Api
        queryset = self.attribute_values(identifiers=identifiers, request=request)
        return queryset

    def update_value(self, identifier, value, *args, **kwargs):
        """ Return a single object, so use '.get()' """
        request = kwargs.get('request', None)
        request.data[identifier] = value
        queryset = self.update_values(identifiers=[identifier], request=request)
        return queryset.get()
