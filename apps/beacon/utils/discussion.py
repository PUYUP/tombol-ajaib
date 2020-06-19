from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from utils.generals import check_uuid, get_model

EnrollmentGuide = get_model('beacon', 'EnrollmentGuide')
EnrollmentChapter = get_model('beacon', 'EnrollmentChapter')
EnrollmentExplain= get_model('beacon', 'EnrollmentExplain')


def get_enrollment_obj(etype=None, uuid=None):
    """ Return enrollment object one of;
    - EnrollmentGuide
    - EnrollmentChapter
    - EnrollmentExplain
    """
    if not etype or not uuid:
        raise ValidationError(_("Enrollment type and UUID required."))

    uuid = check_uuid(uid=uuid)
    if not uuid:
        raise ValidationError(_("UUID invalid."))

    valid_type = ('guide', 'chapter', 'explain')
    if etype not in valid_type:
        raise ValidationError(_("Enrollment type invalid."))

    if etype == 'guide':
        try:
            enrollment_obj = EnrollmentGuide.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise ValidationError(_("Guide enrollment not found."))

    if etype == 'chapter':
        try:
            enrollment_obj = EnrollmentChapter.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise ValidationError(_("Chapter enrollment not found."))

    if etype == 'explain':
        try:
            enrollment_obj = EnrollmentExplain.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise ValidationError(_("Explain enrollment not found."))
    
    if not enrollment_obj:
        raise ValidationError(_("Enrollment not found."))

    # All passed return an object
    return enrollment_obj
