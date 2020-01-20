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
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    creator_uuid = serializers.UUIDField(source='creator.uuid', read_only=True)
    explain_uuid = serializers.UUIDField(read_only=True)
    explain_label = serializers.CharField(read_only=True)
    explain_version = serializers.CharField(read_only=True)
    explain_status = serializers.CharField(read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Explain
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def get_permalink(self, obj):
        reverse_params = {
            'revision_uuid': obj.explain_uuid
        }

        return reverse('explain_revision_detail', kwargs=reverse_params)

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
