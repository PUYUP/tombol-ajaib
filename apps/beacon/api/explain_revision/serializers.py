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
from apps.beacon.utils.constant import DRAFT, REJECTED

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

Explain = get_model('beacon', 'Explain')
ExplainRevision = get_model('beacon', 'ExplainRevision')
Content = get_model('beacon', 'Content')


class ExplainRevisionSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
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
        revision_uuid = data.get('revision_uuid', None)
        person = request.person

        # Validate uuid
        revision_uuid = check_uuid(uid=revision_uuid)
        explain_uuid = check_uuid(uid=explain_uuid)

        """
        Manipulasi;
        Jika revision dengan status DRAFT ada maka ambil dan sunting kembali
        Jika revision dnegan status DRAFT tidak ada maka buat revision baru
        dengan data berasal dari revisi PUBLISHED terakhir
        """
        if revision_uuid and explain_uuid:
            # mutable data
            _mutable = data._mutable
            kwargs['data']._mutable = True

            # get last DRAFT
            revision_obj = ExplainRevision.objects.filter(
                creator=person, explain__uuid=explain_uuid,
                status=DRAFT).first()

            # get current ExplainRevision
            if not revision_obj:
                try:
                    revision_obj = ExplainRevision.objects.get(
                        creator=person, uuid=revision_uuid, explain__uuid=explain_uuid)
                except ObjectDoesNotExist:
                    revision_obj = None

            if revision_obj:
                kwargs['data']['explain'] = revision_obj.explain.pk
                kwargs['data']['label'] = revision_obj.label
                kwargs['data']['changelog'] = revision_obj.changelog
                kwargs['data']['status'] = DRAFT

            context['instance'] = revision_obj
            kwargs['context'] = context

            # set mutable flag back
            kwargs['data']._mutable = _mutable
        super().__init__(*args, **kwargs)

    def get_permalink(self, obj):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # uuid from previous version
        revision_uuid = request.data.get('revision_uuid', None)

        reverse_params = {
            'revision_uuid': obj.uuid
        }

        # redirect to editor if update from previous revision
        if revision_uuid:
            return reverse('explain_revision_editor', kwargs=reverse_params)
        return reverse('explain_revision_detail', kwargs=reverse_params)

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
        person = request.person
        explain_uuid = request.data.get('explain_uuid', None)
        explain_uuid = check_uuid(uid=explain_uuid)

        if not explain_uuid:
            raise NotAcceptable()

        revision_obj, created = ExplainRevision.objects \
            .filter(Q(explain__uuid=explain_uuid), Q(status=DRAFT)) \
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

                # Create content...
                plain = '...'
                blob = plain.encode('utf-8')

                if instance.content:
                    blob = getattr(instance.content, 'blob', plain)

                content = Content.objects.create(creator=person, blob=blob)
                revision_obj.content = content
                revision_obj.save()

        return revision_obj

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
