from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete, post_init


class BeaconConfig(AppConfig):
    name = 'apps.beacon'

    def ready(self):
        from utils.generals import get_model
        from apps.beacon.signals import (
            guide_handler,
            guide_revision_handler,
            explain_handler,
            revision_handler,
            revision_delete_handler)

        # Guid
        Guide = get_model('beacon', 'Guide')
        post_save.connect(
            guide_handler, sender=Guide, dispatch_uid='guide_signal')

        # GuideRevision
        GuideRevision = get_model('beacon', 'GuideRevision')
        post_save.connect(
            guide_revision_handler, sender=GuideRevision,
            dispatch_uid='guide_revision_signal')

        # Explain
        Explain = get_model('beacon', 'Explain')
        post_save.connect(
            explain_handler, sender=Explain, dispatch_uid='explain_signal')

        # ExplainRevision
        ExplainRevision = get_model('beacon', 'ExplainRevision')
        post_save.connect(
            revision_handler, sender=ExplainRevision, dispatch_uid='explain_revision_signal')
        post_delete.connect(
            revision_delete_handler,
            sender=ExplainRevision, dispatch_uid='explain_revision_delete_signal')
