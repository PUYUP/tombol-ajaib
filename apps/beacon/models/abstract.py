import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, STATUS_CHOICES, PUBLISHED, TYPE_CHOICES, PUBLIC)

from .managers import GuideRevisionManager


# 0
class AbstractGuide(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, on_delete=models.SET_NULL,
        related_name='guides')
    category = models.ForeignKey(
        'beacon.Category', null=True, on_delete=models.SET_NULL,
        related_name='guides')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    visibility = models.CharField(
        choices=TYPE_CHOICES, default=PUBLIC, null=True, max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    tags = GenericRelation('beacon.Tag')
    votes = GenericRelation('beacon.Vote')
    ratings = GenericRelation('beacon.Rating')

    objects = GuideRevisionManager()

    class Meta:
        abstract = True
        app_label = 'beacon'
        ordering = ['-date_created']
        verbose_name = _("Guide")
        verbose_name_plural = _("Guides")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)

    def published(self):
        return self.guide_revisions.get(status=PUBLISHED)

    def draft(self):
        return self.guide_revisions.get(status=DRAFT)


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

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, null=True)
    stage = models.BigIntegerField(null=True)
    visibility = models.CharField(
        choices=TYPE_CHOICES, default=PUBLIC, null=True, max_length=255)
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
    visibility = models.CharField(
        choices=TYPE_CHOICES, default=PUBLIC, null=True, max_length=255)
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


# 3
class AbstractSheet(models.Model):
    """Each this object created Sheet created to
    This object only handle for store non-editable by creator"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sheets')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='sheets',
        null=True, blank=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, null=True)
    stage = models.BigIntegerField(null=True)
    visibility = models.CharField(
        choices=TYPE_CHOICES, default=PUBLIC, null=True, max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    votes = GenericRelation('beacon.Vote')
    ratings = GenericRelation('beacon.Rating')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Sheet")
        verbose_name_plural = _("Sheets")

    def __str__(self):
        return self.label
