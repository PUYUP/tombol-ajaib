import inspect

from django.db import transaction
from django.urls import reverse

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

# PROJECT UTILS
from utils.generals import get_model

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

Guide = get_model('beacon', 'Guide')


class GuideSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    permalink_update = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Guide
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def get_permalink_update(self, obj):
        revision = obj.guide_revisions.all().first()
        return reverse('dashboard_guide_detail', kwargs={'guide_uuid': revision.uuid})

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Guide, 'request', request)

        guide_obj = Guide.objects.create(**validated_data)
        return guide_obj


class GuideListSerializer(serializers.ModelSerializer):
    published = serializers.SerializerMethodField(read_only=True)
    draft = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Guide
        fields = '__all__'

    def subquery_attribute(self, obj, identifier=None):
        data = {}
        label = getattr(obj, '%s_label' % identifier, None)

        if label:
            attributes = inspect.getmembers(obj, lambda a:not(inspect.isroutine(a)))

            for item in attributes:
                key = item[0]
                value = item[1]
        
                if key.startswith(identifier):
                    # from this 'identifier_label' to 'label'
                    key = key.replace('%s_' % identifier, '')
                    data[key] = value
            return data
        return None

    def get_published(self, obj):
        return self.subquery_attribute(obj, 'published')

    def get_draft(self, obj):
        return self.subquery_attribute(obj, 'draft')
