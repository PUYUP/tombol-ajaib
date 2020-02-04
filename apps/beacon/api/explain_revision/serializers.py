from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, NotFound

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# LOCAL UTILS
from apps.beacon.utils.constant import DRAFT, REJECTED, PUBLISHED

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')
Content = get_model('beacon', 'Content')


class ExplainRevisionSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    creator_uuid = serializers.UUIDField(source='creator.uuid', read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExplainRevision
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', None)
        context = kwargs.get('context', None)

        request = context.get('request', None)
        explain_uuid = data.get('explain_uuid', None)
        person_pk = request.person_pk

        # Validate uuid
        explain_uuid = check_uuid(uid=explain_uuid)

        """
        With this we create a new Revision
        The data based on last PUBLISHED or DRAFT previous revisions
        """
        if explain_uuid:
            # mutable data
            _mutable = data._mutable
            kwargs['data']._mutable = True

            # get last DRAFT or PUBLISHED
            revision_obj = ExplainRevision.objects \
                .filter(
                    Q(creator_id=person_pk), Q(explain__uuid=explain_uuid),
                    Q(status=DRAFT) | Q(status=PUBLISHED)).first()

            # Prepare new DRAFT data
            if revision_obj:
                kwargs['data']['explain'] = revision_obj.explain_id
                kwargs['data']['label'] = revision_obj.label
                kwargs['data']['changelog'] = revision_obj.changelog
                kwargs['data']['status'] = DRAFT

            context['instance'] = revision_obj
            kwargs['context'] = context

            # set mutable flag back
            kwargs['data']._mutable = _mutable
        super().__init__(*args, **kwargs)

    def get_permalink(self, obj):
        return reverse('explain_detail', kwargs={'explain_uuid': obj.uuid})

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        setattr(ExplainRevision, 'request', request)

        # get variable
        label = request.data.get('label', None)
        person_pk = request.person_pk
        explain_uuid = request.data.get('explain_uuid', None)
        explain_uuid = check_uuid(uid=explain_uuid)

        if not explain_uuid:
            raise NotAcceptable(detail=_("Explain UUID invalid."))

        obj, created = ExplainRevision.objects \
            .filter(Q(explain__uuid=explain_uuid), Q(status=DRAFT)) \
            .get_or_create(**validated_data, defaults={'label': label})

        if obj and created:
            # get instance from init
            instance = self.context.get('instance', None)

            if instance:
                # Create content...
                plain = '...'
                blob = plain.encode('utf-8')

                if instance.content:
                    blob = getattr(instance.content, 'blob', plain)

                content = Content.objects.create(creator_id=person_pk, blob=blob)
                obj.content = content
                obj.save()

        return obj

    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # only revision with status is DRAFT allow to update
        if instance.status != DRAFT:
            raise NotAcceptable(detail=_("Revisi sudah terpublikasi. Tindakan ditolak."))

        # include all field for update
        for item in validated_data:
            value = validated_data.get(item, None)
            if value:
                setattr(instance, item, value)

        plain = request.data.get('content_blob', None)
        blob = plain.encode('utf-8')
        content = getattr(instance, 'content', None)

        if content:
            content.blob = blob
            content.save()
            instance.content = content

        instance.save()
        return instance
