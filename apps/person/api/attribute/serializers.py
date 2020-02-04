from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

# PROJECT UTILS
from utils.generals import get_model

Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')
AttributeOptionGroup = get_model('person', 'AttributeOptionGroup')


class OptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOptionGroup
        fields = '__all__'


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    """ Serialize Attribute, not user
    Only user as Person show """
    option_group = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(
        view_name='persons:attribute-detail', lookup_field='uuid', read_only=True)

    class Meta:
        model = Attribute
        fields = ('uuid', 'label', 'value', 'url', 'option_group', 'field_type',
                  'identifier',)

    def get_option_group(self, obj):
        # option_group
        option_group = getattr(obj, 'option_group', None)
        if option_group:
            request = self.context['request']
            field_type = obj.field_type
            person_pk = request.person_pk

            selected_option = AttributeValue.objects.filter(
                object_id=person_pk,
                attribute__identifier=obj.identifier,
                **{'value_%s__id' % field_type: OuterRef('id')})

            options = obj.option_group.options \
                .annotate(
                    selected=Exists(selected_option)) \
                .all().values('id', 'uuid', 'option', 'selected')
            return options
        return None

    def get_value(self, obj):
        field_type = obj.field_type
        request = self.context['request']
        person_pk = request.person_pk
        value_field = 'value_%s' % field_type
        value = getattr(obj, value_field, '')

        if person_pk and field_type != 'multi_option' and field_type != 'option':
            if field_type == 'image' or field_type == 'file':
                try:
                    obj_file = obj.attributevalue_set.get(
                        object_id=person_pk, attribute__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # File exists
                if obj_file:
                    file = getattr(obj_file, 'value_%s' % field_type, None)
                    if file:
                        value = request.build_absolute_uri(file.url)

            value_dict = {
                'uuid': getattr(obj, 'value_uuid', None),
                'field': field_type,
                'print': value,
            }

            return value_dict
        return None

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        identifier = instance.identifier
        value = request.data.get('value', None)
        person_pk = request.person_pk

        if person_pk:
            queryset = Attribute.objects.update_value(
                identifier, value, request=request)
            return queryset
        return validated_data
