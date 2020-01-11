import uuid
import asyncio
import urllib
import json

from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator)
from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _

# PROJECT UTILS
from utils.generals import get_model

from .generals import random_string
from .senders import (
    send_verification_email,
    send_verification_sms,
    send_password_email,
    send_secure_email
)

Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')
SecureCode = get_model('person', 'SecureCode')
UserModel = get_user_model()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class CurrentPersonDefault:
    """Return current logged-in person"""
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        if hasattr(user, 'person'):
            self.person = user.person
        else:
            self.person = None

    def __call__(self):
        return self.person

    def __repr__(self):
        return '%s()' % self.__class__.__name__


def check_validation_passed(self, *agrs, **kwargs):
    request = kwargs.get('request', None)
    if not request:
        return False

    person = getattr(request.user, 'person', None)
    if not person:
        return False

    content_type = ContentType.objects.get_for_model(person)
    validation_type = Validation.objects.filter(required=True)

    if not validation_type.exists():
        return True

    validation_value = ValidationValue.objects.filter(
        Q(validation__required=True),
        Q(is_verified=True),
        Q(content_type=content_type.pk),
        Q(object_id=person.pk))

    # Compare validation type with the value
    # If value same indicated all validation passed
    return validation_type.count() == validation_value.count()


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, person, timestamp):
        return (
            six.text_type(person.uuid) + six.text_type(timestamp)
        )


account_verification_token = TokenGenerator()


def get_user_from_email(self, email=None):
    """Given an email, return matching user(s)
    who should receive a secure code."""
    if email:
        try:
            user = UserModel.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None
        return user
    return None


def get_user_from_uuid(self, person_uuid=None):
    """Get person object by uuid"""
    if person_uuid is None:
        return None

    try:
        person_uuid = uuid.UUID(person_uuid)
    except ValueError:
        return None

    try:
        user = UserModel.objects.get(person__uuid=person_uuid)
    except ObjectDoesNotExist:
        user = None
    return user


def get_person_uuid(self, secure_code=None):
    """Get person uuid from secure code"""
    if not secure_code:
        return None

    try:
        secure_code_obj = SecureCode.objects.get(secure_code=secure_code)
    except ObjectDoesNotExist:
        return None

    return secure_code_obj.person.uuid


def get_person_from_secure_code(self, *args, **kwargs):
    """Get person from secure code"""
    secure_code = kwargs.get('secure_code', None)
    if not secure_code:
        return None

    person_uuid = get_person_uuid(self, secure_code=secure_code)
    if person_uuid is None:
        return None

    # Now get person by uuid
    try:
        user = UserModel.objects.get(person__uuid=person_uuid)
    except ObjectDoesNotExist:
        return None

    person = getattr(user, 'person', None)
    if person:
        return person
    return None


def create_secure_code(self, *args, **kwargs):
    """Generate secure code"""
    context = dict()
    email = kwargs.get('email', None)
    identifier = kwargs.get('identifier', None)

    if not email or not identifier:
        return None

    # Get user from email if not logged in
    if self.request.user.is_authenticated:
        user = self.request.user
    else:
        user = get_user_from_email(self, email)
        if user is None:
            return None

    # Person exist in user
    person = getattr(user, 'person', None)
    if person:
        secure_code_obj, created = SecureCode.objects.update_or_create(
            person=person,
            identifier=identifier,
            is_used=False,
            defaults={'identifier': identifier, 'is_used': False})

        secure_code = secure_code_obj.secure_code
        secure_hash = secure_code_obj.secure_hash

        # Fill secure code if used for validation value
        content_type = ContentType.objects.get_for_model(person)

        try:
            validation_obj = ValidationValue.objects.select_for_update().get(
                validation__identifier=identifier,
                object_id=person.pk,
                content_type=content_type.pk)

            validation_obj.secure_code = secure_code
            validation_obj.save()

            # Set content type for secure code
            secure_code_obj.content_object = validation_obj
        except ObjectDoesNotExist:
            pass

        # Return data
        context['person_uuid'] = urlsafe_base64_encode(
            force_bytes(person.uuid))
        context['token'] = account_verification_token.make_token(person)
        context['secure_code'] = secure_code
        context['secure_hash'] = secure_hash

        # Append secure code to request
        setattr(self.request, 'secure_code', secure_code)
        setattr(self.request, 'person', person)
        return context
    return None


def validate_secure_code(self, *agrs, **kwargs):
    """Validate secure code valid or not
    If valid return True, and invalid return None"""
    secure_code = kwargs.get('secure_code', None)
    secure_hash = kwargs.get('secure_hash', None)

    if not secure_code or not secure_hash:
        return None

    person = get_person_from_secure_code(self, secure_code=secure_code)

    try:
        secure_code_obj = SecureCode.objects.select_for_update().get(
            person=person,
            secure_code=secure_code,
            secure_hash=secure_hash,
            is_used=False)
    except ObjectDoesNotExist:
        return None

    # Update to used!
    secure_code_obj.is_used = True
    secure_code_obj.save()
    return True


def send_secure_code(self, *args, **kwargs):
    # 'auto'' = Auto (with email), 'sms' = Manual (with SMS), 'manual' = By admin
    method = kwargs.get('method', None)
    email = kwargs.get('email', None)
    new_value = kwargs.get('new_value', None)
    user = kwargs.get('user', None)
    identifier = kwargs.get('identifier', None)

    if not method and not user:
        return None

    person = getattr(user, 'person', None)
    if person:
        # Generate secure code
        # Whatever method, email used for check use exist
        secure_data = create_secure_code(self, email=email, identifier=identifier)
        if not secure_data:
            return None

        # Collect data for email
        params = {
            'user': user,
            'request': self.request,
            'email': email,
            'new_value': new_value,
            'label': _("Verifikasi")
        }

        # Send with email
        if method == 'email':
            loop.run_in_executor(None, send_verification_email, params)

        # Send with SMS
        if method == 'sms':
            loop.run_in_executor(None, send_verification_sms, params)

        return secure_data
    return None


def mark_secure_code_used(self, *agrs, **kwargs):
    secure_code = kwargs.get('secure_code', None)
    person_pk = kwargs.get('person_pk', None)

    if secure_code and person_pk:
        try:
            secure_code_obj = SecureCode.objects.select_for_update().get(
                person__pk=person_pk,
                secure_code=secure_code,
                is_used=False)

            secure_code_obj.is_used = True
            secure_code_obj.save()
        except ObjectDoesNotExist:
            pass
