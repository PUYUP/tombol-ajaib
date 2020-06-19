from django.db import transaction, IntegrityError
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import (
    ObjectDoesNotExist, ValidationError as _ValidationError)
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

# DRF
from rest_framework import serializers
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError

# PROJECT UTILS
from utils.generals import get_model, check_uuid

# PERSON APP UTILS
from apps.person.utils.auths import CurrentPersonDefault

# LOCAL UTILS
from apps.beacon.utils.discussion import get_enrollment_obj

Topic = get_model('beacon', 'Topic')
EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')
EnrollmentChapter = get_model('beacon', 'EnrollmentChapter')
EnrollmentExplain= get_model('beacon', 'EnrollmentExplain')


class TopicSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=CurrentPersonDefault())
    permalink = serializers.SerializerMethodField(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='beacons:topic-detail', lookup_field='uuid', read_only=True)

    class Meta:
        model = Topic
        fields = '__all__'
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context', None)
        request = context.get('request', None)

        if request.method == 'POST':
            data = kwargs.get('data', None)
            enrollment_uuid = data.get('enrollment_uuid', None)
            enrollment_type = data.get('enrollment_type', None)

            try:
                enrollment_obj = get_enrollment_obj(etype=enrollment_type, uuid=enrollment_uuid)
            except _ValidationError as e:
                raise NotAcceptable(' '.join(e))

            if enrollment_obj:
                # mutable data
                _mutable = getattr(data, '_mutable', None)
                if _mutable:
                    kwargs['data']._mutable = True

                model_name = enrollment_obj._meta.model_name
                content_type = ContentType.objects.get(app_label='beacon', model=model_name)

                kwargs['data']['object_id'] = enrollment_obj.id
                kwargs['data']['content_type'] = content_type.id

                context['instance'] = enrollment_obj
                kwargs['context'] = context

                # set mutable flag back
                if _mutable:
                    kwargs['data']._mutable = _mutable

        super().__init__(*args, **kwargs)

    def get_permalink(self, obj):
        params = {
            'guide_uuid': obj.content_object.guide.uuid,
            'topic_uuid': obj.uuid
        }
        return reverse('guide_topic_detail', kwargs=params)

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable(detail=_("Request not defined."))

        # Append request to objects
        setattr(Topic, 'request', request)

        try:
            obj = Topic.objects.create(**validated_data)
        except IntegrityError:
            raise NotAcceptable(detail=_("Integrity error."))

        return obj

    def update(self, instance, validated_data):
        # include all field for update
        for item in validated_data:
            value = validated_data.get(item, None)
            if value:
                setattr(instance, item, value)

        instance.save()
        return instance
