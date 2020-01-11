from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import DRAFT

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

Introduction = get_model('beacon', 'Introduction')
GuideRevision = get_model('beacon', 'GuideRevision')


class IntroductionSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Introduction
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', None)
        object_id = data.get('object_id', None)
        model_name = data.get('model_name', None)

        if object_id and model_name:
            # mutable data
            _mutable = data._mutable
            kwargs['data']._mutable = True

            content_type = ContentType.objects.get(app_label='beacon', model=model_name)
            kwargs['data']['content_type'] = content_type.pk

            # set mutable flag back
            kwargs['data']._mutable = _mutable
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        setattr(Introduction, 'request', request)

        introduction_obj = Introduction.objects.create(**validated_data)
        return introduction_obj

    def update(self, instance, validated_data):
        # include all field for update
        for item in validated_data:
            value = validated_data.get(item, None)
            if value:
                setattr(instance, item, value)

        instance.save()
        return instance
