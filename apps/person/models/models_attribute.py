import os
import uuid
from datetime import date, datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator, validate_email, URLValidator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.core.files import File
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.text import slugify

# PROJECTS UTILS
from utils.generals import non_python_keyword, get_model

# LOCAL UTILS
from ..utils.constant import FIELD_TYPE_CHOICES
from ..utils.attributes import AttributeManager


def entity_directory_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images/<entity>_<id>/<filename>
    object_id = instance.object_id
    ct = ContentType.objects.get_for_id(instance.content_type.pk)
    obj = ct.get_object_for_this_type(pk=object_id)

    model_class = instance.content_type.model_class()
    model_name = slugify(model_class._meta.model_name)
    model_uuid = obj.uuid
    return 'images/{0}_{1}/{2}'.format(model_name, model_uuid, filename)


def entity_directory_file_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/files/<entity>_<id>/<filename>
    object_id = instance.object_id
    ct = ContentType.objects.get_for_id(instance.content_type.pk)
    obj = ct.get_object_for_this_type(pk=object_id)

    model_class = instance.content_type.model_class()
    model_name = slugify(model_class._meta.model_name)
    model_uuid = obj.uuid
    return 'files/{0}_{1}/{2}'.format(model_name, model_uuid, filename)


# Create your models here.
class AbstractAttribute(models.Model):
    """
    Attribute for entity filter by content_type
    """
    roles = models.ManyToManyField(
        'person.Role',
        blank=True,
        limit_choices_to=Q(is_active=True),
        help_text=_("Limit attributes by Roles."))
    content_type = models.ManyToManyField(
        ContentType, related_name='person_attibutes',
        limit_choices_to=Q(app_label='person'))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(_('Label'), max_length=128)
    identifier = models.SlugField(
        _('Identifier'), max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ])
    field_type = models.CharField(
        choices=FIELD_TYPE_CHOICES,
        default=FIELD_TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))
    option_group = models.ForeignKey(
        'person.AttributeOptionGroup',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='person_attributes',
        verbose_name=_("Option Group"),
        help_text=_('Select option group if using '
                    'type "Option" or "Multi Option"'))
    instruction = models.TextField(_('Instruction'), blank=True, null=True)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    is_secured = models.BooleanField(_('Secured'), default=False)
    is_required = models.BooleanField(_('Required'), default=False)

    # Extend manager
    objects = AttributeManager()

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')

    def __str__(self):
        return self.label


class AbstractAttributeValue(models.Model):
    """Mapping value with entity"""
    attribute = models.ForeignKey(
        'person.Attribute',
        on_delete=models.CASCADE,
        verbose_name=_("Attribute"))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    value_text = models.CharField(
        _('Text'), blank=True, null=True, max_length=255)
    value_email = models.EmailField(
        _('Email'), blank=True, null=True, max_length=255)
    value_url = models.URLField(
        _('URL'), blank=True, null=True, max_length=500)
    value_integer = models.IntegerField(
        _('Integer'), blank=True, null=True, db_index=True)
    value_boolean = models.NullBooleanField(
        _('Boolean'), blank=True, db_index=True)
    value_float = models.FloatField(
        _('Float'), blank=True, null=True, db_index=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(
        _('Date'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(
        _('DateTime'), blank=True, null=True, db_index=True)
    value_multi_option = models.ManyToManyField(
        'person.AttributeOption',
        blank=True,
        related_name='multi_valued_attribute_values',
        verbose_name=_("Value multi option"))
    value_option = models.ForeignKey(
        'person.AttributeOption',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Value option"))
    value_file = models.FileField(
        upload_to=entity_directory_file_path, max_length=255,
        blank=True, null=True)
    value_image = models.ImageField(
        upload_to=entity_directory_image_path, max_length=255,
        blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    # Generic foreignkey
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='person'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ('attribute', 'content_type', 'object_id')
        verbose_name = _('Attribute value')
        verbose_name_plural = _('Attribute values')

    def __str__(self):
        return self.summary()

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.field_type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    value = property(_get_value)

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in entity summaries.
        """
        return "%s: %s" % (self.attribute.label, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_label = '_%s_as_text' % self.attribute.field_type
        return getattr(self, property_label, self.value)


class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type

    For example, Language
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(_('Label'), max_length=128)
    identifier = models.SlugField(
        _('Identifier'), max_length=128, null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ])

    def __str__(self):
        return self.label

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Attribute option group')
        verbose_name_plural = _('Attribute option groups')

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        'person.AttributeOptionGroup',
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ('group', 'option')
        verbose_name = _('Attribute option')
        verbose_name_plural = _('Attribute options')

    def __str__(self):
        return self.option
