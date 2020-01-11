import uuid
import base64
import sys

from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, PUBLISHED, STATUS_CHOICES)


# 0
class AbstractSection(models.Model):
    """Each this object created Revision created to
    This object only handle for store non-editable by creator"""
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sections')
    chapter = models.ForeignKey(
        'beacon.Chapter',
        on_delete=models.CASCADE,
        related_name='sections')
    label = models.CharField(max_length=255, null=True)
    stage = models.BigIntegerField(null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic relations
    votes = GenericRelation('beacon.Vote')
    ratings = GenericRelation('beacon.Rating')

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Section")
        verbose_name_plural = _("Sections")

    def __str__(self):
        return self.label

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


# 1
class AbstractContent(models.Model):
    creator = models.ForeignKey(
        'person.Person', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='contents')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    blob = models.BinaryField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'beacon'
        verbose_name = _("Section Content")
        verbose_name_plural = _("Section Contents")

    def __str__(self):
        if self.blob:
            return '%s B' % sys.getsizeof(self.blob)
        return super().__str__()

    def save(self, *args, **kwargs):
        # Convert blob to bytes
        if self.blob and type(self.blob) is not bytes:
            self.blob = bytes(self.blob, 'utf-8')
        super().save(*args, **kwargs)
