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

Guide = get_model('beacon', 'Guide')
GuideRevision = get_model('beacon', 'GuideRevision')


class GuideRevisionSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    creator_uuid = serializers.UUIDField(source='creator.uuid', read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GuideRevision
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', None)
        context = kwargs.get('context', None)

        request = context.get('request', None)
        guide_uuid = data.get('guide_uuid', None)
        person_pk = request.person_pk

        # Validate uuid
        guide_uuid = check_uuid(uid=guide_uuid)

        # With this we create a new Revision
        # The data based on last PUBLISHED or DRAFT previous revisions
        if guide_uuid:
            # mutable data
            _mutable = getattr(data, '_mutable', None)
            if not _mutable:
                kwargs['data']._mutable = True

            # get last DRAFT or PUBLISHED
            revision_obj = GuideRevision.objects \
                .filter(
                    Q(creator_id=person_pk), Q(guide__uuid=guide_uuid),
                    Q(status=DRAFT) | Q(status=PUBLISHED)).first()

            # Prepare new DRAFT data
            if revision_obj:
                kwargs['data']['guide'] = revision_obj.guide_id
                kwargs['data']['label'] = revision_obj.label
                kwargs['data']['description'] = revision_obj.description
                kwargs['data']['changelog'] = revision_obj.changelog
                kwargs['data']['status'] = DRAFT

            context['instance'] = revision_obj
            kwargs['context'] = context

            # set mutable flag back
            if not _mutable:
                kwargs['data']._mutable = _mutable
        super().__init__(*args, **kwargs)

    """
    def to_internal_value(self, data):
        context = self.context

        request = context.get('request', None)
        if not request:
            raise NotAcceptable(detail=_("Request not define."))

        # With this we create a new Revision
        # The data based on last PUBLISHED or DRAFT previous revisions
        person_pk = request.person_pk
        guide_uuid = data.get('guide_uuid', None)
        guide_uuid = check_uuid(uid=guide_uuid)

        if not guide_uuid:
            raise NotAcceptable(detail=_("Guide UUID invalid."))

        # get last DRAFT or PUBLISHED
        revision_obj = GuideRevision.objects \
            .filter(
                Q(creator_id=person_pk), Q(guide__uuid=guide_uuid),
                Q(status=DRAFT) | Q(status=PUBLISHED)).first()

        # un-mutable data
        print(data.copy())
        _mutable = getattr(data, '_mutable', None)
        if not _mutable:
            data._mutable = True

        # Prepare new DRAFT data
        if revision_obj:
            data['guide'] = revision_obj.guide_id
            data['label'] = revision_obj.label
            data['description'] = revision_obj.description
            data['changelog'] = revision_obj.changelog
            data['status'] = DRAFT

            self.context['instance'] = revision_obj

        # set mutable back
        if not _mutable:
            data._mutable = _mutable
        return super().to_internal_value(data)
    """

    def get_permalink(self, obj):
        return reverse('chapter_detail', kwargs={'chapter_uuid': obj.uuid})

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable(detail=_("Request not define."))

        # Append request to objects
        setattr(GuideRevision, 'request', request)

        # get variable
        person_pk = request.person_pk
        label = request.data.get('label', None)
        guide_uuid = request.data.get('guide_uuid', None)
        guide_uuid = check_uuid(uid=guide_uuid)

        if not guide_uuid:
            raise NotAcceptable(detail=_("Guide UUID invalid."))

        # If Revision with DRAFT status appear, get it
        # If not create new
        obj, created = GuideRevision.objects \
            .filter(Q(guide__uuid=guide_uuid), Q(status=DRAFT)) \
            .get_or_create(**validated_data, defaults={'label': label})

        # If revision is new we need create Introductions
        # And then assign them
        if obj and created:
            # get instance from init
            instance = self.context.get('instance', None)

            if instance:
                introductions = instance.introductions \
                    .prefetch_related('creator', 'creator__user', 'content_type') \
                    .select_related('creator', 'creator__user', 'content_type') \
                    .all()

                if introductions.exists():
                    intro_model = introductions.model
                    intro_collection = list()

                    for item in introductions:
                        intro_obj = intro_model(
                            creator_id=person_pk,
                            content_object=obj,
                            description=item.description)
                        intro_collection.append(intro_obj)
                    intro_model.objects.bulk_create(intro_collection)
        return obj

    def update(self, instance, validated_data):
        # only revision with status is DRAFT allow to update
        if instance.status != DRAFT:
            raise NotAcceptable(detail=_("Revisi sudah terpublikasi. Tindakan ditolak."))

        # include all field for update
        for item in validated_data:
            value = validated_data.get(item, None)
            if value:
                setattr(instance, item, value)

        instance.save()
        return instance
