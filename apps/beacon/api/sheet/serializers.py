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
Sheet = get_model('beacon', 'Sheet')
SheetRevision = get_model('beacon', 'SheetRevision')


class SheetSerializer(serializers.ModelSerializer):
    published = serializers.SerializerMethodField(read_only=True)
    draft = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Sheet
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
            setattr(Sheet, 'request', request)

        sheet_params = dict()
        sheet_fields = ('pk', 'uuid', 'label', 'version', 'status')
        sheet_revisions = SheetRevision.objects.filter(sheet__pk=OuterRef('pk'))

        for item in sheet_fields:
            sheet_params['sheet_%s' % item] = Case(
                When(num_revision=1, then=Subquery(sheet_revisions.values(item)[:1])),
                default=Subquery(sheet_revisions.filter(status=PUBLISHED).values(item)[:1])
            )

        obj = Sheet.objects.create(**validated_data)
        sheet_obj = Sheet.objects \
            .annotate(num_revision=Count('sheet_revisions'), **sheet_params).get(pk=obj.pk)
        return sheet_obj

    def get_published(self, obj):
        return self.subquery_attribute(obj, 'published')

    def get_draft(self, obj):
        return self.subquery_attribute(obj, 'draft')
