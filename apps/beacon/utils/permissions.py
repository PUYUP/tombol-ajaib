from django.utils.translation import ugettext_lazy as _

# DRF
from rest_framework import permissions

# PROJECTS UTILS
from utils.generals import get_model

Guide = get_model('beacon', 'Guide')


class IsAllowCrudObject(permissions.BasePermission):
    def has_permission(self, request, view):
        basename = getattr(view, 'basename', None)
        basename_clean = basename.replace('_', '')

        if hasattr(request.user, 'person'):
            if (
                request.user.has_perm('person.add_%s' % basename_clean) and
                request.user.has_perm('person.change_%s' % basename_clean) and
                request.user.has_perm('person.delete_%s' % basename_clean)
            ):
                return True
        return False
