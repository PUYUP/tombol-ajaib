from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete, post_init


class BeaconConfig(AppConfig):
    name = 'apps.beacon'

    def ready(self):
        from utils.generals import get_model
        from apps.beacon.signals import (
            guide_handler,
            chapter_handler,
            explain_handler,
            topic_handler,
            reply_handler)

        # Guide
        Guide = get_model('beacon', 'Guide')
        post_save.connect(
            guide_handler, sender=Guide, dispatch_uid='guide_signal')

        # Chapter
        Chapter = get_model('beacon', 'Chapter')
        post_save.connect(
            chapter_handler, sender=Chapter, dispatch_uid='chapter_signal')

        # Explain
        Explain = get_model('beacon', 'Explain')
        post_save.connect(
            explain_handler, sender=Explain, dispatch_uid='explain_signal')

        # Topic
        Topic = get_model('beacon', 'Topic')
        post_save.connect(
            topic_handler, sender=Topic, dispatch_uid='topic_signal')

        # Reply
        Reply = get_model('beacon', 'Reply')
        post_save.connect(
            reply_handler, sender=Reply, dispatch_uid='reply_signal')
