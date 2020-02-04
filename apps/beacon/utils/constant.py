from django.utils.translation import ugettext_lazy as _

# STATUS
PENDING = 'pending'
REVIEWED = 'reviewed'
PUBLISHED = 'published'
RETURNED = 'returned'
REJECTED = 'rejected'
DRAFT = 'draft'
ARCHIVE = 'archive'
STATUS_CHOICES = (
    (PENDING, _("Tertunda")),
    (REVIEWED, _("Ditinjau")),
    (PUBLISHED, _("Terbit")),
    (RETURNED, _("Dikembalikan")),
    (REJECTED, _("Ditolak")),
    (DRAFT, _("Konsep")),
    (ARCHIVE, _("Arsip")),
)

# TYPE
PRIVATE = 'private'
PUBLIC = 'public'
TYPE_CHOICES = (
    (PRIVATE, _("Privat")),
    (PUBLIC, _("Publik")),
)
