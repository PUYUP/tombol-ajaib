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
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Guide
        fields = ('label', 'category', 'creator', 'url',)
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def get_url(self, obj):
        revision = obj.guide_revisions.all().first()
        return reverse('guide_revision_editor', kwargs={'revision_uuid': revision.uuid})

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
