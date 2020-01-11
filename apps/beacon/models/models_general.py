import uuid

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

# LOCAL UTILS
from apps.beacon.utils.files import (
    directory_file_path,
    directory_image_path)


# 0
class AbstractTag(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='tags')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('label',)
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.label
    
    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)


# 1
class AbstractVote(models.Model):
    UP_VOTE = 'U'
    DOWN_VOTE = 'D'
    VOTE_TYPES = (
        (UP_VOTE, _("Up Vote")),
        (DOWN_VOTE, _("Down Vote")),
    )

    vote_type = models.CharField(max_length=1, choices=VOTE_TYPES)
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='votes')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('object_id', 'creator',)
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")

    def __str__(self):
        return self.get_vote_type_display


# 2
class AbstractRating(models.Model):
    ONE_STAR = 1
    TWO_STAR = 2
    THREE_STAR = 3
    FOUR_STAR = 4
    FIVE_STAR = 5
    SCORE_CHOICES = (
        (ONE_STAR, _("Terburuk")),
        (TWO_STAR, _("Buruk")),
        (THREE_STAR, _("Sedang")),
        (FOUR_STAR, _("Baik")),
        (FIVE_STAR, _("Sangat Baik")),
    )

    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='ratings')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    score = models.PositiveIntegerField(choices=SCORE_CHOICES)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('object_id', 'creator',)
        ordering = ('-date_updated',)
        verbose_name = _('Rating')
        verbose_name_plural = _('Ratings')

    def __str__(self):
        return self.get_score_display


# 3
class AbstractCategory(models.Model):
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='childs',
        limit_choices_to={'parent__isnull': True})
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        unique_together = ('label',)
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.label
    
    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)


# 4
class AbstractAttachment(models.Model):
    """General attachment used for various objects"""
    creator = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name='attachments')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    value_image = models.ImageField(
        upload_to=directory_image_path,
        max_length=500, null=True, blank=True)
    value_file = models.FileField(
        upload_to=directory_file_path,
        max_length=500, null=True, blank=True)
    featured = models.BooleanField(null=True)
    caption = models.TextField(max_length=500, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'beacon'
        ordering = ('-date_updated',)
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self):
        value = None

        if self.value_image:
            value = self.value_image.url

        if self.value_file:
            value = self.value_file.url

        return value


# 5
class AbstractIntroduction(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='introductions')
    order = models.BigIntegerField(null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    description = models.TextField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='beacon'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Introduction")
        verbose_name_plural = _("Introductions")

    def __str__(self):
        return self.description
