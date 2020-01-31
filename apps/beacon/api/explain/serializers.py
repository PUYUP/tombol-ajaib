import inspect

from django.db import transaction
from django.db.models import Value, Case, When, Subquery, OuterRef, Count
from django.urls import reverse

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

Guide = get_model('beacon', 'Guide')
Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')


class ExplainSerializer(serializers.ModelSerializer):
    chapter_uuid = serializers.UUIDField(source='chapter.uuid', read_only=True)
    published = serializers.SerializerMethodField(read_only=True)
    draft = serializers.SerializerMethodField(read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Explain
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
            setattr(Explain, 'request', request)

        explain_params = dict()
        explain_fields = ('pk', 'uuid', 'label', 'version', 'status')
        explain_revisions = ExplainRevision.objects.filter(explain__pk=OuterRef('pk'))

        for item in explain_fields:
            explain_params['explain_%s' % item] = Case(
                When(num_revision=1, then=Subquery(explain_revisions.values(item)[:1])),
                default=Subquery(explain_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        obj = Explain.objects.create(**validated_data)
        explain_obj = Explain.objects \
            .annotate(num_revision=Count('explain_revisions'), **explain_params).get(pk=obj.pk)
        return explain_obj

    def get_published(self, obj):
        return self.subquery_attribute(obj, 'published')

    def get_draft(self, obj):
        return self.subquery_attribute(obj, 'draft')

    def get_permalink(self, obj):
        return reverse('explain_detail', kwargs={'explain_uuid': obj.uuid})
