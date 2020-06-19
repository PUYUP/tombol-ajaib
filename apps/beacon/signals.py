def guide_handler(sender, instance, created, **kwargs):
    if created and instance:
        instance.create_revision()


def chapter_handler(sender, instance, created, **kwargs):
    if created and instance:
        instance.create_revision()


def explain_handler(sender, instance, created, **kwargs):
    if created and instance:
        instance.create_revision()

def topic_handler(sender, instance, created, **kwargs):
    if created and instance:
        instance.create_revision()

def reply_handler(sender, instance, created, **kwargs):
    if created and instance:
        instance.create_revision()
