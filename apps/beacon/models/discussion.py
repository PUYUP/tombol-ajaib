import uuid

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify


# 0
class AbstractTopic(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='topics')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    content_blob = models.BinaryField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    tags = GenericRelation('beacon.Tag')
    votes = GenericRelation('beacon.Vote')
    attachments = GenericRelation('beacon.Attachment')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('label',)
        verbose_name = _("Discussion Topic")
        verbose_name_plural = _("Discussion Topics")

    def __str__(self):
        return self.label
    
    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        # Convert content_blob to bytes
        if self.content_blob and type(self.content_blob) is not bytes:
            self.content_blob = bytes(self.content_blob, 'utf-8')

        super().save(*args, **kwargs)


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
        related_name='replies')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(editable=False, max_length=500)
    content_blob = models.BinaryField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    votes = GenericRelation('beacon.Vote')
    attachments = GenericRelation('beacon.Attachment')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('label',)
        verbose_name = _("Discussion Reply")
        verbose_name_plural = _("Discussion Replies")

    def __str__(self):
        return self.label
    
    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        # Convert content_blob to bytes
        if self.content_blob and type(self.content_blob) is not bytes:
            self.content_blob = bytes(self.content_blob, 'utf-8')

        super().save(*args, **kwargs)
