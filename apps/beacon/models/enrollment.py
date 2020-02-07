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
class AbstractGuideEnrollment(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='guide_enrollments')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='guide_enrollments')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Guide Enrollment")
        verbose_name_plural = _("Guide Enrollments")

    def __str__(self):
        return self.guide.label


# 1
class AbstractChapterEnrollment(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='chapter_enrollments')
    enrollment = models.ForeignKey(
        'beacon.GuideEnrollment',
        on_delete=models.CASCADE,
        related_name='chapter_enrollments')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='chapter_enrollments')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='chapter_enrollments')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Chapter Enrollment")
        verbose_name_plural = _("Chapter Enrollments")

    def __str__(self):
        return self.chapter.label


# 2
class AbstractExplainEnrollment(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='explain_enrollments')
    enrollment = models.ForeignKey(
        'beacon.GuideEnrollment',
        on_delete=models.CASCADE,
        related_name='explain_enrollments')
    guide = models.ForeignKey(
        'beacon.Guide',
        on_delete=models.CASCADE,
        related_name='explain_enrollments')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='explain_enrollments')
    explain = models.ForeignKey(
        'beacon.Explain',
        on_delete=models.CASCADE,
        related_name='explain_enrollments')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_begin = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Explain Enrollment")
        verbose_name_plural = _("Explain Enrollments")

    def __str__(self):
        return self.explain.label
