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
        fields = '__all__'

    def get_option_group(self, obj):
        # option_group
        option_group = getattr(obj, 'option_group', None)
        if option_group:
            request = self.context['request']
            field_type = obj.field_type
            person = getattr(request.user, 'person', None)

            selected_option = AttributeValue.objects.filter(
                object_id=person.pk,
                attribute__identifier=obj.identifier,
                **{'value_%s__pk' % field_type: OuterRef('id')})

            options = obj.option_group.options \
                .annotate(
                    selected=Exists(selected_option)) \
                .all().values('id', 'option', 'selected')
            return options
        return None

    def get_value(self, obj):
        field_type = obj.field_type
        request = self.context['request']
        person = getattr(request.user, 'person', None)
        value_field = 'value_%s' % field_type
        value = getattr(obj, value_field, None)
        value_print = getattr(obj, 'label', None)

        if person:
            if field_type == 'image' or field_type == 'file':
                try:
                    obj_file = obj.attributevalue_set.get(
                        person=person, attribute__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # File exists
                if obj_file:
                    file = getattr(obj_file, 'value_%s' % field_type, None)
                    if file:
                        value = request.build_absolute_uri(file.url)
                        value_print = file.name

            if field_type == 'multi_option':
                value = list()
                value_print = list()
                option = obj.attributevalue_set \
                    .prefetch_related('person', 'attribute',
                                      'value_multi_option', 'content_object') \
                    .select_related('person', 'attribute',
                                    'value_multi_option', 'content_object') \
                    .filter(
                        person=person,
                        attribute__identifier=obj.identifier) \
                    .defer('person', 'attribute', 'value_multi_option',
                           'content_object') \
                    .values(
                        'value_multi_option__id',
                        'value_multi_option__option')

                if option:
                    for opt in option:
                        id = opt.get('value_multi_option__id', None)
                        label = opt.get('value_multi_option__option', None)
                        value.append(id)
                        value_print.append(label)

            value_dict = {
                'uuid': getattr(obj, 'value_uuid', None),
                'field': field_type,
                'object': value,
                'object_print': value_print
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
        person = getattr(request.user, 'person', None)
        content_type = ContentType.objects.get_for_model(person)

        if person:
            data = {identifier: value}
            Attribute.objects.update_value(data, person, content_type)

            return Attribute.objects \
                .get_attribute(identifier, person, content_type)
        return validated_data
