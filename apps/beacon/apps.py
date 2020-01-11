from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete, post_init


class BeaconConfig(AppConfig):
    name = 'apps.beacon'

    def ready(self):
        from utils.generals import get_model
        from apps.beacon.signals import (
            guide_handler,
            guide_revision_handler,
            section_handler,
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

        # Section
        Section = get_model('beacon', 'Section')
        post_save.connect(
            section_handler, sender=Section, dispatch_uid='section_signal')

        # SectionRevision
        SectionRevision = get_model('beacon', 'SectionRevision')
        post_save.connect(
            revision_handler, sender=SectionRevision, dispatch_uid='section_revision_signal')
        post_delete.connect(
            revision_delete_handler,
            sender=SectionRevision, dispatch_uid='section_revision_delete_signal')
