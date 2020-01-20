from .models_general import *
from .models_abstract import *
from .models_revission import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()

# 0
if not is_model_registered('beacon', 'Tag'):
    class Tag(AbstractTag):
        class Meta(AbstractTag.Meta):
            db_table = 'guides_tag'

    __all__.append('Tag')


# 1
if not is_model_registered('beacon', 'Vote'):
    class Vote(AbstractVote):
        class Meta(AbstractVote.Meta):
            db_table = 'guides_vote'

    __all__.append('Vote')


# 2
if not is_model_registered('beacon', 'Rating'):
    class Rating(AbstractRating):
        class Meta(AbstractRating.Meta):
            db_table = 'guides_rating'

    __all__.append('Rating')


# 3
if not is_model_registered('beacon', 'Category'):
    class Category(AbstractCategory):
        class Meta(AbstractCategory.Meta):
            db_table = 'guides_category'

    __all__.append('Category')


# 4
if not is_model_registered('beacon', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'guides_attachment'

    __all__.append('Attachment')


# 5
if not is_model_registered('beacon', 'Introduction'):
    class Introduction(AbstractIntroduction):
        class Meta(AbstractIntroduction.Meta):
            db_table = 'guides_introduction'

    __all__.append('Introduction')


# 6
if not is_model_registered('beacon', 'Guide'):
    class Guide(AbstractGuide):
        class Meta(AbstractGuide.Meta):
            db_table = 'guides_guide'

    __all__.append('Guide')


# 7
if not is_model_registered('beacon', 'Chapter'):
    class Chapter(AbstractChapter):
        class Meta(AbstractChapter.Meta):
            db_table = 'guides_chapter'

    __all__.append('Chapter')


# 8
if not is_model_registered('beacon', 'Explain'):
    class Explain(AbstractExplain):
        class Meta(AbstractExplain.Meta):
            db_table = 'guides_explain'

    __all__.append('Explain')


# 9
if not is_model_registered('beacon', 'Content'):
    class Content(AbstractContent):
        class Meta(AbstractContent.Meta):
            db_table = 'guides_content'

    __all__.append('Content')


# 11
if not is_model_registered('beacon', 'GuideRevision'):
    class GuideRevision(AbstractGuideRevision):
        class Meta(AbstractGuideRevision.Meta):
            db_table = 'guides_guide_revision'

    __all__.append('GuideRevision')


# 12
if not is_model_registered('beacon', 'ExplainRevision'):
    class ExplainRevision(AbstractExplainRevision):
        class Meta(AbstractExplainRevision.Meta):
            db_table = 'guides_explain_revision'

    __all__.append('ExplainRevision')


# 13
if not is_model_registered('beacon', 'ChapterRevision'):
    class ChapterRevision(AbstractChapterRevision):
        class Meta(AbstractChapterRevision.Meta):
            db_table = 'guides_chapter_revision'

    __all__.append('ChapterRevision')
