from django.db import transaction
from django.db.models import Q, Case, When, Subquery, OuterRef, Count
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

Chapter = get_model('beacon', 'Chapter')
ChapterRevision = get_model('beacon', 'ChapterRevision')


class ChapterRevisionSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    creator_uuid = serializers.UUIDField(source='creator.uuid', read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChapterRevision
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', None)
        context = kwargs.get('context', None)

        request = context.get('request', None)
        chapter_uuid = data.get('chapter_uuid', None)
        person_pk = request.person_pk

        # Validate uuid
        chapter_uuid = check_uuid(uid=chapter_uuid)

        """
        With this we create a new Revision
        The data based on last PUBLISHED or DRAFT previous revisions
        """
        if chapter_uuid:
            # mutable data
            _mutable = getattr(data, '_mutable', None)
            if _mutable:
                kwargs['data']._mutable = True

            # get last DRAFT or PUBLISHED
            revision_obj = ChapterRevision.objects \
                .filter(
                    Q(creator_id=person_pk), Q(chapter__uuid=chapter_uuid),
                    Q(status=DRAFT) | Q(status=PUBLISHED)).first()

            # Prepare new DRAFT data
            if revision_obj:
                kwargs['data']['chapter'] = revision_obj.chapter_id
                kwargs['data']['label'] = revision_obj.label
                kwargs['data']['description'] = revision_obj.description
                kwargs['data']['changelog'] = revision_obj.changelog
                kwargs['data']['status'] = DRAFT

            context['instance'] = revision_obj
            kwargs['context'] = context

            # set mutable flag back
            if _mutable:
                kwargs['data']._mutable = _mutable
        super().__init__(*args, **kwargs)

    def get_permalink(self, obj):
        return reverse('chapter_detail', kwargs={'chapter_uuid': obj.chapter.uuid})

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        setattr(ChapterRevision, 'request', request)

        # get variable
        label = request.data.get('label', None)
        chapter_uuid = request.data.get('chapter_uuid', None)
        chapter_uuid = check_uuid(uid=chapter_uuid)

        if not chapter_uuid:
            raise NotAcceptable(detail=_("Chapter UUID invalid."))

        # If Revision with DRAFT status appear, get it
        # If not create new
        obj, created = ChapterRevision.objects \
            .filter(Q(chapter__uuid=chapter_uuid), Q(status=DRAFT)) \
            .get_or_create(**validated_data, defaults={'label': label})

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
