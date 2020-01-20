from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

# DRF
from rest_framework import permissions

# PROJECTS UTILS
from utils.generals import get_model

AttributeValue = get_model('person', 'AttributeValue')
Validation = get_model('person', 'Validation')


class IsAllowCrudObject(permissions.BasePermission):
    def has_permission(self, request, view):
        basename = getattr(view, 'basename', None)
        basename_clean = basename.replace('_', '')

        if hasattr(request.user, 'person'):
            if (
                request.user.has_perm('person.add_%svalue' % basename_clean) and
                request.user.has_perm('person.change_%svalue' % basename_clean) and
                request.user.has_perm('person.delete_%svalue' % basename_clean)
            ):
                return True
        return False


class IsOwnerOrReject(permissions.BasePermission):
    """
    Validate current user is self
    If not access read only
    """

    def has_permission(self, request, view):
        # Staff can always access CRUD
        if request.user.is_staff:
            return True

        # Only as person allowed
        if hasattr(request.user, 'person'):
            user_uuid = request.user.person.uuid
            current_uuid = view.kwargs['uuid']

            try:
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False
            return current_uuid == user_uuid
        return False


class IsAccountValidated(permissions.BasePermission):
    message = _("Akun belum tervalidasi.")

    def has_permission(self, request, view):
        person = request.person
        if not person:
            return False

        is_verified = True
        content_type = ContentType.objects.get_for_model(person)
        validations = Validation.objects.check_validations(person, content_type)

        for item in validations:
            if item.is_verified == False:
                is_verified = item.is_verified
                break
        return is_verified
