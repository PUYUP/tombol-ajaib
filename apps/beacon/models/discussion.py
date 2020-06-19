import uuid

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

# LOCAL UTILS
from apps.beacon.utils.constant import DRAFT


# 0
class AbstractTopic(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='topics')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Generic relations
    tags = GenericRelation('beacon.Tag')
    votes = GenericRelation('beacon.Vote')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('label',)
        verbose_name = _("Discussion Topic")
        verbose_name_plural = _("Discussion Topics")

    def __str__(self):
        return self.label

    def create_revision(self):
        self.topic_revisions.model.objects.create(
            topic=self,
            creator=self.creator,
            version=1,
            label=self.label,
            status=DRAFT,
            changelog=_("Initial"),
            content_type=self.content_type,
            object_id=self.object_id)


# 1
class AbstractReply(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='replies')
    topic = models.ForeignKey(
        'beacon.Topic',
        on_delete=models.CASCADE,
        related_name='replies')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True, blank=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Generic relations
    votes = GenericRelation('beacon.Vote')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('label',)
        verbose_name = _("Discussion Reply")
        verbose_name_plural = _("Discussion Replies")

    def __str__(self):
        return self.label

    def create_revision(self):
        self.reply_revisions.model.objects.create(
            reply=self,
            creator=self.creator,
            topic=self.topic,
            version=1,
            label=self.label,
            status=DRAFT,
            changelog=_("Initial"),
            content_type=self.content_type,
            object_id=self.object_id)
