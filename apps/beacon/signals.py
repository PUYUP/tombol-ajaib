from django.utils.translation import ugettext_lazy as _

# PROJECT UTILS
from utils.generals import get_model

# LOCAL UTILS
from apps.beacon.utils.constant import DRAFT, PUBLISHED


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


def guide_revision_handler(sender, instance, created, **kwargs):
    """ Jika belum ada status PUBLISHED maka sunting saja
    Jika sudah ada status PUBLISHED maka buat revision baru """

    """
    model = instance._meta.model
    guide = instance.guide
    label = instance.label
    description = instance.description
    changelog = instance.changelog
    status = instance.status
    version = instance.version + 1

    queryset = model.objects.filter(
        creator=instance.creator,
        guide=instance.guide)
    published_count = queryset.filter(status=PUBLISHED).count()

    if not created and published_count > 0:
        data = {
            'version': version,
            'label': label,
            'description': description,
            'status': status,
            'changelog': changelog
        }

        new_revision = model.objects.create(guide=guide, **data)
        if new_revision.status == PUBLISHED:
            instance.status = DRAFT
            instance.save()
    """
    pass


def explain_handler(sender, instance, created, **kwargs):
    """
    if created and instance:
        instance.revisions.create(
            creator=instance.creator, label=instance.label)
    """
    pass


def revision_handler(sender, instance, created, **kwargs):
    """
    if created and instance:
        changelog = ChangeLog.objects.create(
            creator=instance.creator,
            description=_("Initial"))

        instance.changelog = changelog
        instance.save()
    """
    pass


def revision_delete_handler(sender, instance, **kwargs):
    """
    changelog = getattr(instance, 'changelog', None)
    if changelog:
        changelog.delete()
    """
    pass
