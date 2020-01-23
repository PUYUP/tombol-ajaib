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
        fields = ('label', 'category', 'creator', 'permalink_update',)
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def get_permalink_update(self, obj):
        revision = obj.guide_revisions.all().first()
        return reverse('dashboard_guide_detail', kwargs={'guide_revision_uuid': revision.uuid})

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
    permalink = serializers.SerializerMethodField(read_only=True)
    last_updated = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Guide
        fields = '__all__'

    def get_permalink(self, obj):
        return reverse('guide_revision_detail', kwargs={'revision_uuid': obj.revision_uuid})

    def get_last_updated(self, obj):
        if obj.explain_date_created and obj.chapter_date_created:
            if obj.explain_date_created >= obj.chapter_date_created:
                return obj.explain_date_created
            elif obj.explain_date_created <= obj.chapter_date_created:
                return obj.chapter_date_created
            else:
                return obj.date_created
        return obj.date_created
