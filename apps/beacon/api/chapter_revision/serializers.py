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

        if data:
            request = context.get('request', None)
            chapter_uuid = data.get('chapter_uuid', None)
            revision_uuid = data.get('revision_uuid', None)
            person = request.person

            # Validate uuid
            revision_uuid = check_uuid(uid=revision_uuid)
            chapter_uuid = check_uuid(uid=chapter_uuid)

            """
            Manipulasi;
            Jika revision dengan status DRAFT ada maka ambil dan sunting kembali
            Jika revision dnegan status DRAFT tidak ada maka buat revision baru
            dengan data berasal dari revisi PUBLISHED terakhir
            """
            if revision_uuid and chapter_uuid:
                # mutable data
                _mutable = data._mutable
                kwargs['data']._mutable = True

                # get last DRAFT
                revision_obj = ChapterRevision.objects.filter(
                    creator=person, chapter__uuid=chapter_uuid,
                    status=DRAFT).first()

                # get current ChapterRevision
                if not revision_obj:
                    try:
                        revision_obj = ChapterRevision.objects.get(
                            creator=person, uuid=revision_uuid, chapter__uuid=chapter_uuid)
                    except ObjectDoesNotExist:
                        revision_obj = None

                if revision_obj:
                    kwargs['data']['chapter'] = revision_obj.chapter.pk
                    kwargs['data']['label'] = revision_obj.label
                    kwargs['data']['description'] = revision_obj.description
                    kwargs['data']['changelog'] = revision_obj.changelog
                    kwargs['data']['status'] = DRAFT

                context['instance'] = revision_obj
                kwargs['context'] = context

                # set mutable flag back
                kwargs['data']._mutable = _mutable
        super().__init__(*args, **kwargs)

    def get_permalink(self, obj):
        print(obj)
        reverse_params = {
            'revision_uuid': obj.uuid
        }

        return reverse('chapter_revision_detail', kwargs=reverse_params)

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
        person = request.person
        chapter_uuid = request.data.get('chapter_uuid', None)
        chapter_uuid = check_uuid(uid=chapter_uuid)

        revision_obj, created = ChapterRevision.objects \
            .filter(Q(chapter__uuid=chapter_uuid), Q(status=DRAFT)) \
            .get_or_create(**validated_data, defaults={'label': label})

        if revision_obj and created:
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
                            creator=person,
                            content_object=revision_obj,
                            description=item.description)
                        intro_collection.append(intro_obj)
                    intro_model.objects.bulk_create(intro_collection)
        return revision_obj

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
