import uuid
from pprint import pprint

from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, STATUS_CHOICES, PUBLISHED)


# 0
class AbstractGuide(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, on_delete=models.SET_NULL,
        related_name='guide')
    category = models.ForeignKey(
        'beacon.Category', null=True, on_delete=models.SET_NULL,
        related_name='guide')
    label = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    votes = GenericRelation('beacon.Vote')
    ratings = GenericRelation('beacon.Rating')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Guide")
        verbose_name_plural = _("Guides")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)


# 1
class AbstractChapter(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='chapters')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='chapters')

    label = models.CharField(max_length=255, null=True)
    stage = models.BigIntegerField(null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Chapter")
        verbose_name_plural = _("Chapters")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)


# 2
class AbstractExplain(models.Model):
    """Each this object created Revision created to
    This object only handle for store non-editable by creator"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='explains')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='explains',
        null=True, blank=True)
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='explains')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, null=True)
    stage = models.BigIntegerField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    votes = GenericRelation('beacon.Vote')
    ratings = GenericRelation('beacon.Rating')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Explain")
        verbose_name_plural = _("Explains")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        guide_from_chapter = self.chapter.guide
        self.guide = guide_from_chapter

        super().save(*args, **kwargs)

    def get_latest_revision(self):
        revision = self.revisions.filter(status=PUBLISHED) \
            .order_by('-date_created')

        if revision.exists():
            return revision.last()
        return None

    def get_latest_content(self):
        revision = self.get_latest_revision()
        content = getattr(revision, 'content', None)

        if revision and content:
            blob = getattr(content, 'blob', None)
            if blob and type(blob) is bytes:
                return blob.decode('utf-8')
            return blob
        return None

    def get_latest_label(self):
        revision = self.get_latest_revision()
        if revision:
            return revision.label
        return self.label
