from django.db import models

# LOCAL UTILS
from apps.beacon.utils.constant import (
    DRAFT, STATUS_CHOICES, PUBLISHED)


class GuideRevisionManager(models.Manager):
    def published(self):
        x = self.revisions.get(status=PUBLISHED)
        print(x)
        return 'AAAAA'

    def create_revision(self):
        print('OO')
