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

from ..chapter_revision.serializers import ChapterRevisionSerializer
from ..explain.serializers import ExplainSerializer

Guide = get_model('beacon', 'Guide')
Chapter = get_model('beacon', 'Chapter')
ChapterRevision = get_model('beacon', 'ChapterRevision')


class ChapterSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    published = serializers.SerializerMethodField(read_only=True)
    draft = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chapter
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

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

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Chapter, 'request', request)

        obj = Chapter.objects.create(**validated_data)
        return obj

    def get_published(self, obj):
        return self.subquery_attribute(obj, 'published')

    def get_draft(self, obj):
        return self.subquery_attribute(obj, 'draft')

class ChapterCreateSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    revisions = ChapterRevisionSerializer(read_only=True, many=True)

    class Meta:
        model = Chapter
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Chapter, 'request', request)

        obj = Chapter.objects.create(**validated_data)
        return obj
