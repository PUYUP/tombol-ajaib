from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q

# PROJECT UTILS
from utils.generals import get_model

UserModel = get_user_model()
AttributeValue = get_model('person', 'AttributeValue')
Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')


# Create signals
def user_handler(sender, instance, created, **kwargs):
    if not created:
        person = getattr(instance, 'person', None)

        if person:
            try:
                validation_type = Validation.objects.get(identifier='email')
            except ObjectDoesNotExist:
                validation_type = None

            if validation_type:
                content_type = ContentType.objects.get_for_model(person)
                validation_value, created = ValidationValue.objects \
                    .update_or_create(
                        validation=validation_type,
                        object_id=person.pk,
                        content_type=content_type)
                validation_value.value_email = instance.email
                validation_value.save()


def person_handler(sender, instance, created, **kwargs):
    user = getattr(instance, 'user', None)
    is_register = getattr(instance, 'is_register', None)

    if is_register and user:
        try:
            validation_type = Validation.objects.get(identifier='email')
        except ObjectDoesNotExist:
            validation_type = None
        
        if validation_type:
            content_type = ContentType.objects.get_for_model(instance)
            validation_value, created = ValidationValue.objects \
                .update_or_create(
                    validation=validation_type,
                    object_id=instance.pk,
                    content_type=content_type,
                    is_verified=False)
            validation_value.value_email = user.email
            validation_value.save()


def attribute_handler(sender, instance, created, **kwargs):
    pass


def person_roles_handler(sender, **kwargs):
    pass


def group_handler(sender, instance, created, **kwargs):
    pass
