import uuid
import base64
import sys

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, ARCHIVE, STATUS_CHOICES)


# 0
class AbstractGuideRevision(models.Model):
    """Each Guide maybe has hundred revisions
    But for displayed to reader use the last with published status"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='guide_revisions')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='guide_revisions')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.IntegerField(editable=False, null=True, default=0)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    description = models.TextField(max_length=500, blank=True, null=True)
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=100, default=DRAFT)
    changelog = models.TextField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    introductions = GenericRelation('beacon.Introduction')
    attachments = GenericRelation('beacon.Attachment')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Guide Revision")
        verbose_name_plural = _("Guide Revisions")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        model = self._meta.model

        revisions = model.objects \
            .filter(
                creator=self.creator, guide=self.guide) \
            .exclude(pk=self.pk) \
            .order_by('-version') \

        if revisions.exists():
            # make other revisions status to Arcive
            if self.status == PUBLISHED:
                revisions.update(status=ARCHIVE)

            # increase version
            if not self.pk:
                revisions_last = revisions.first()
                self.version = revisions_last.version + 1

        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)


# 1
class AbstractChapterRevision(models.Model):
    """Each Chapter maybe has hundred revisions
    But for displayed to reader use the last with published status"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='chapter_revisions')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='chapter_revisions')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='chapter_revisions')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.IntegerField(editable=False, null=True, default=0)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    description = models.TextField(max_length=500, blank=True, null=True)
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=100, default=DRAFT)
    changelog = models.TextField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    introductions = GenericRelation('beacon.Introduction')
    attachments = GenericRelation('beacon.Attachment')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Chapter Revision")
        verbose_name_plural = _("Chapter Revisions")

    def __str__(self):
        return self.label

    
    def save(self, *args, **kwargs):
        model = self._meta.model

        revisions = model.objects \
            .filter(
                creator=self.creator, chapter=self.chapter) \
            .exclude(pk=self.pk) \
            .order_by('-version') \

        if revisions.exists():
            # make other revisions status to Arcive
            if self.status == PUBLISHED:
                revisions.update(status=ARCHIVE)

            # increase version
            if not self.pk:
                revisions_last = revisions.first()
                self.version = revisions_last.version + 1

        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        # Set guide
        guide_from_chapter = self.chapter.guide
        self.guide = guide_from_chapter

        super().save(*args, **kwargs)


# 2
class AbstractExplainRevision(models.Model):
    """Each Explain maybe has hundred revisions
    But for displayed to reader use the last with published status"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='explain_revisions')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='explain_revisions')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name='explain_revisions')
    explain = models.ForeignKey(
        'beacon.Explain',
        on_delete=models.CASCADE,
        related_name='explain_revisions')
    content = models.OneToOneField(
        'beacon.Content',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='explain_revisions')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.IntegerField(editable=False, null=True, default=0)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=100, default=DRAFT)
    changelog = models.TextField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    introductions = GenericRelation('beacon.Introduction')
    attachments = GenericRelation('beacon.Attachment')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Explain Revision")
        verbose_name_plural = _("Explain Revisions")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        model = self._meta.model

        revisions = model.objects \
            .filter(
                creator=self.creator, explain=self.explain) \
            .exclude(pk=self.pk) \
            .order_by('-version') \

        if revisions.exists():
            # make other revisions status to Arcive
            if self.status == PUBLISHED:
                revisions.update(status=ARCHIVE)

            # increase version
            if not self.pk:
                revisions_last = revisions.first()
                self.version = revisions_last.version + 1

        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        # Set guide
        guide_from_explain = self.explain.guide
        self.guide = guide_from_explain

        # Set chapter
        chapter_from_explain = self.explain.chapter
        self.chapter = chapter_from_explain

        super().save(*args, **kwargs)


# 3
class AbstractSheetRevision(models.Model):
    """Each Sheet maybe has hundred revisions
    But for displayed to reader use the last with published status"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sheet_revisions')
    sheet = models.ForeignKey(
        'beacon.Sheet',
        on_delete=models.CASCADE,
        related_name='sheet_revisions')
    content = models.OneToOneField(
        'beacon.Content',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sheet_revisions')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.IntegerField(editable=False, null=True, default=0)
    label = models.CharField(max_length=255)
    slug = models.SlugField(editable=False, max_length=500)
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=100, default=DRAFT)
    changelog = models.TextField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    attachments = GenericRelation('beacon.Attachment')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Sheet Revision")
        verbose_name_plural = _("Sheet Revisions")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        model = self._meta.model

        revisions = model.objects \
            .filter(
                creator=self.creator, sheet=self.sheet) \
            .exclude(pk=self.pk) \
            .order_by('-version') \

        if revisions.exists():
            # make other revisions status to Arcive
            if self.status == PUBLISHED:
                revisions.update(status=ARCHIVE)

            # increase version
            if not self.pk:
                revisions_last = revisions.first()
                self.version = revisions_last.version + 1

        # Auto create slug from label
        if self.label:
            self.slug = slugify(self.label)

        super().save(*args, **kwargs)
