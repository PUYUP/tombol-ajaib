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
class AbstractEnrollmentGuide(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='enrollment_guides')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='enrollment_guides')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Enrollment Guide")
        verbose_name_plural = _("Enrollment Guides")

    def __str__(self):
        return self.guide.label


# 1
class AbstractEnrollmentChapter(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='enrollment_chapters')
    enrollment_guide = models.ForeignKey(
        'beacon.EnrollmentGuide',
        on_delete=models.CASCADE,
        related_name='enrollment_chapters')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='enrollment_chapters')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='enrollment_chapters')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Enrollment Chapter")
        verbose_name_plural = _("Enrollment Chapters")

    def __str__(self):
        return self.chapter.label

    def save(self, *args, **kwargs):
        self.guide = self.enrollment_guide.guide
        super().save(*args, **kwargs)


# 2
class AbstractEnrollmentExplain(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='enrollment_explains')
    enrollment_guide = models.ForeignKey(
        'beacon.EnrollmentGuide',
        on_delete=models.CASCADE,
        related_name='enrollment_explains')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='enrollment_explains')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='enrollment_explains')
    explain = models.ForeignKey(
        'beacon.Explain',
        on_delete=models.CASCADE,
        related_name='enrollment_explains')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_begin = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Enrollment Explain")
        verbose_name_plural = _("Enrollment Explains")

    def __str__(self):
        return self.explain.label

    def save(self, *args, **kwargs):
        self.guide = self.enrollment_guide.guide
        self.chapter = self.explain.chapter
        super().save(*args, **kwargs)
