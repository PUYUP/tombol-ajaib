from django.utils.translation import ugettext_lazy as _

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from apps.beacon.utils.constant import DRAFT, PUBLISHED

Content = get_model('beacon', 'Content')


def guide_handler(sender, instance, created, **kwargs):
    if created and instance:
        description = None
        request = getattr(instance, 'request', None)
        if request:
            description = request.data.get('description', None)

        instance.guide_revisions.model.objects.create(
            guide=instance, creator=instance.creator, version=1,
            label=instance.label, description=description,
            status=DRAFT, changelog=_("Initial"))


def chapter_handler(sender, instance, created, **kwargs):
    if created and instance:
        status = DRAFT
        description = None
        changelog = None

        request = getattr(instance, 'request', None)
        if request:
            status = request.data.get('status', DRAFT)
            description = request.data.get('description', None)
            changelog = request.data.get('changelog', _("Initial"))

        instance.chapter_revisions.model.objects.create(
            chapter=instance, creator=instance.creator, version=1,
            label=instance.label, description=description,
            status=status, changelog=changelog)


def explain_handler(sender, instance, created, **kwargs):
    if created and instance:
        status = DRAFT
        changelog = None

        request = getattr(instance, 'request', None)
        if request:
            status = request.data.get('status', DRAFT)
            changelog = request.data.get('changelog', _("Initial"))

        # Create blob content
        content = Content.objects.create(creator=instance.creator)

        instance.explain_revisions.model.objects.create(
            explain=instance, creator=instance.creator, version=1,
            label=instance.label, status=status,
            changelog=changelog, content=content)
