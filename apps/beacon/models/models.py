from .general import *
from .guide import *
from .revision import *
from .enrollment import *
from .discussion import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()

# 0
if not is_model_registered('beacon', 'Tag'):
    class Tag(AbstractTag):
        class Meta(AbstractTag.Meta):
            db_table = 'beacon_tag'

    __all__.append('Tag')


# 1
if not is_model_registered('beacon', 'Vote'):
    class Vote(AbstractVote):
        class Meta(AbstractVote.Meta):
            db_table = 'beacon_vote'

    __all__.append('Vote')


# 2
if not is_model_registered('beacon', 'Rating'):
    class Rating(AbstractRating):
        class Meta(AbstractRating.Meta):
            db_table = 'beacon_rating'

    __all__.append('Rating')


# 3
if not is_model_registered('beacon', 'Category'):
    class Category(AbstractCategory):
        class Meta(AbstractCategory.Meta):
            db_table = 'beacon_category'

    __all__.append('Category')


# 4
if not is_model_registered('beacon', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'beacon_attachment'

    __all__.append('Attachment')


# 5
if not is_model_registered('beacon', 'Introduction'):
    class Introduction(AbstractIntroduction):
        class Meta(AbstractIntroduction.Meta):
            db_table = 'beacon_introduction'

    __all__.append('Introduction')


# 6
if not is_model_registered('beacon', 'Guide'):
    class Guide(AbstractGuide):
        class Meta(AbstractGuide.Meta):
            db_table = 'beacon_guide'

    __all__.append('Guide')


# 7
if not is_model_registered('beacon', 'Chapter'):
    class Chapter(AbstractChapter):
        class Meta(AbstractChapter.Meta):
            db_table = 'beacon_chapter'

    __all__.append('Chapter')


# 8
if not is_model_registered('beacon', 'Explain'):
    class Explain(AbstractExplain):
        class Meta(AbstractExplain.Meta):
            db_table = 'beacon_explain'

    __all__.append('Explain')


# 9
if not is_model_registered('beacon', 'Content'):
    class Content(AbstractContent):
        class Meta(AbstractContent.Meta):
            db_table = 'beacon_content'

    __all__.append('Content')


# 11
if not is_model_registered('beacon', 'GuideRevision'):
    class GuideRevision(AbstractGuideRevision):
        class Meta(AbstractGuideRevision.Meta):
            db_table = 'beacon_guide_revision'

    __all__.append('GuideRevision')


# 12
if not is_model_registered('beacon', 'ExplainRevision'):
    class ExplainRevision(AbstractExplainRevision):
        class Meta(AbstractExplainRevision.Meta):
            db_table = 'beacon_explain_revision'

    __all__.append('ExplainRevision')


# 13
if not is_model_registered('beacon', 'ChapterRevision'):
    class ChapterRevision(AbstractChapterRevision):
        class Meta(AbstractChapterRevision.Meta):
            db_table = 'beacon_chapter_revision'

    __all__.append('ChapterRevision')


# 14
if not is_model_registered('beacon', 'Sheet'):
    class Sheet(AbstractSheet):
        class Meta(AbstractSheet.Meta):
            db_table = 'beacon_sheet'

    __all__.append('Sheet')


# 15
if not is_model_registered('beacon', 'SheetRevision'):
    class SheetRevision(AbstractSheetRevision):
        class Meta(AbstractSheetRevision.Meta):
            db_table = 'beacon_sheet_revision'

    __all__.append('SheetRevision')


# 16
if not is_model_registered('beacon', 'EnrollmentGuide'):
    class EnrollmentGuide(AbstractEnrollmentGuide):
        class Meta(AbstractEnrollmentGuide.Meta):
            db_table = 'beacon_enrollment_guide'

    __all__.append('EnrollmentGuide')


# 17
if not is_model_registered('beacon', 'EnrollmentChapter'):
    class EnrollmentChapter(AbstractEnrollmentChapter):
        class Meta(AbstractEnrollmentChapter.Meta):
            db_table = 'beacon_enrollment_chapter'

    __all__.append('EnrollmentChapter')


# 18
if not is_model_registered('beacon', 'EnrollmentExplain'):
    class EnrollmentExplain(AbstractEnrollmentExplain):
        class Meta(AbstractEnrollmentExplain.Meta):
            db_table = 'beacon_enrollment_explain'

    __all__.append('EnrollmentExplain')


# 19
if not is_model_registered('beacon', 'Topic'):
    class Topic(AbstractTopic):
        class Meta(AbstractTopic.Meta):
            db_table = 'beacon_discuss_topic'

    __all__.append('Topic')


# 20
if not is_model_registered('beacon', 'TopicRevision'):
    class TopicRevision(AbstractTopicRevision):
        class Meta(AbstractTopicRevision.Meta):
            db_table = 'beacon_discuss_topic_revision'

    __all__.append('TopicRevision')


# 21
if not is_model_registered('beacon', 'Reply'):
    class Reply(AbstractReply):
        class Meta(AbstractReply.Meta):
            db_table = 'beacon_discuss_reply'

    __all__.append('Reply')


# 22
if not is_model_registered('beacon', 'ReplyRevision'):
    class ReplyRevision(AbstractReplyRevision):
        class Meta(AbstractReplyRevision.Meta):
            db_table = 'beacon_discuss_reply_revision'

    __all__.append('ReplyRevision')
