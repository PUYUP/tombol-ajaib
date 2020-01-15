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
Chapter = get_model('beacon', 'Chapter')
ChapterRevision = get_model('beacon', 'ChapterRevision')


class ChapterSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())

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
