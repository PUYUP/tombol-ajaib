import uuid

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.core.files import File
from django.core.validators import RegexValidator, validate_email, URLValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import Q

# PROJECTS UTILS
from utils.generals import non_python_keyword, get_model

# LOCAL UTILS
from ..utils.constant import (
    FIELD_VALIDATION_CHOICES, VERIFICATION_METHOD)
from ..utils.generals import random_string
from ..utils.validations import ValidationManager


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


class AbstractValidation(models.Model):
    """Validation for entity filter by content_type"""
    roles = models.ManyToManyField(
        'person.Role',
        blank=True,
        limit_choices_to=Q(is_active=True),
        help_text=_("Limit validations by Roles."))
    content_type = models.ManyToManyField(
        ContentType, related_name='person_validations',
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
        choices=FIELD_VALIDATION_CHOICES,
        default=FIELD_VALIDATION_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))
    instruction = models.TextField(_('Instruction'), blank=True)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    is_secured = models.BooleanField(_('Secured'), default=False)
    is_required = models.BooleanField(_('Required'), default=False)
    is_unique = models.BooleanField(_('Unique'), default=True)
    method = models.CharField(
        max_length=255, null=True,
        choices=VERIFICATION_METHOD,
        help_text=_("Verification method"))

    # Extend manager
    objects = ValidationManager()

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Validation')
        verbose_name_plural = _('Validations')

    def __str__(self):
        return self.label


class AbstractValidationValue(models.Model):
    """Mapping value with entity"""
    validation = models.ForeignKey(
        'person.Validation',
        on_delete=models.CASCADE,
        verbose_name=_("Validation"))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    secure_code = models.CharField(max_length=128, null=True, blank=True)
    is_verified = models.BooleanField(null=True)
    value_text = models.CharField(
        _('Text'), blank=True, null=True, max_length=255)
    value_email = models.EmailField(
        _('Email'), blank=True, null=True, max_length=255)
    value_url = models.URLField(
        _('URL'), blank=True, null=True, max_length=500)
    value_integer = models.IntegerField(
        _('Integer'), blank=True, null=True, db_index=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
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
        unique_together = ('validation', 'content_type', 'object_id')
        verbose_name = _('Validation value')
        verbose_name_plural = _('Validation values')

    def __str__(self):
        return self.summary()

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.validation.field_type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    value = property(_get_value)

    def summary(self):
        """
        Gets a string representation of both the validation and it's value,
        used e.g in entity summaries.
        """
        return "%s: %s" % (self.validation.label, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the validation's value. To customise
        e.g. image validation values, declare a _image_as_text property and
        return something appropriate.
        """
        property_label = '_%s_as_text' % self.validation.field_type
        return getattr(self, property_label, self.value)


class AbstractSecureCode(models.Model):
    """Secure code for critical action
    Each action has own secure code
    Hashing use password"""
    person = models.ForeignKey(
        'person.Person',
        on_delete=models.CASCADE)
    secure_hash = models.CharField(max_length=255)
    secure_code = models.CharField(max_length=255)
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
    is_used = models.BooleanField()
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    # Generic foreignkey
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        limit_choices_to=Q(app_label='person'),
        null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Secure code')
        verbose_name_plural = _('Secure codes')

    def __str__(self):
        return self.secure_code

    def save(self, *args, **kwargs):
        secure_code = random_string()
        content_type = self.content_type
        object_id = self.object_id

        # After used can't change again
        if not self.is_used:
            self.secure_code = secure_code
            self.secure_hash = make_password(secure_code)

        if object_id and content_type:
            md = content_type.model_class()

            try:
                md_obj = md.objects.get(pk=object_id)
                md_obj.secure_code = secure_code
                md_obj.save()
            except ObjectDoesNotExist:
                pass

        super().save(*args, **kwargs)
