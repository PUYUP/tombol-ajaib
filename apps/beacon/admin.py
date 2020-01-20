from django.contrib import admin

# PROJECT UTILS
from utils.generals import get_model

# PERSON MODEL
Person = get_model('person', 'Person')

# BEACON MODEL
Tag = get_model('beacon', 'Tag')
Vote = get_model('beacon', 'Vote')
Rating = get_model('beacon', 'Rating')
Category = get_model('beacon', 'Category')
Attachment = get_model('beacon', 'Attachment')
Introduction = get_model('beacon', 'Introduction')
Guide = get_model('beacon', 'Guide')
Chapter = get_model('beacon', 'Chapter')
Explain = get_model('beacon', 'Explain')
Content = get_model('beacon', 'Content')
GuideRevision = get_model('beacon', 'GuideRevision')
ChapterRevision = get_model('beacon', 'ChapterRevision')
ExplainRevision = get_model('beacon', 'ExplainRevision')


# ...
# GuideRevision
# ...
class GuideRevisionAdmin(admin.ModelAdmin):
    """Extend media admin"""
    model = GuideRevision
    readonly_fields = ('version', 'uuid',)
    list_filter = ('status',)
    list_display = ('label', 'status', 'version', 'date_created', 'date_updated',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator', 'creator__user', 'guide') \
            .select_related('creator', 'creator__user', 'guide')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# ...
# Introduction
# ...
class IntroductionAdmin(admin.ModelAdmin):
    """Extend media admin"""
    model = Introduction
    readonly_fields = ('uuid',)
    list_display = ('description', 'date_created', 'date_updated',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator', 'creator__user', 'content_type') \
            .select_related('creator', 'creator__user', 'content_type')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# ...
# Chapter
# ...
class ChapterAdmin(admin.ModelAdmin):
    """Extend media admin"""
    model = Chapter
    readonly_fields = ('uuid',)
    list_display = ('label', 'date_created', 'date_updated',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator', 'creator__user', 'guide') \
            .select_related('creator', 'creator__user', 'guide')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# ...
# ChapterRevision
# ...
class ChapterRevisionAdmin(admin.ModelAdmin):
    """Extend media admin"""
    model = ChapterRevision
    readonly_fields = ('version', 'uuid',)
    list_display = ('label', 'status', 'version', 'chapter', 'date_created', 'date_updated',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'chapter':
            kwargs['queryset'] = Chapter.objects.prefetch_related('creator', 'creator__user') \
                .select_related('creator', 'creator__user')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator', 'creator__user', 'chapter') \
            .select_related('creator', 'creator__user', 'chapter')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# ...
# Explain
# ...
class ExplainAdmin(admin.ModelAdmin):
    model = Explain
    readonly_fields = ('uuid',)
    list_display = ('label', 'chapter', 'guide', 'date_created', 'date_updated',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'guide':
            kwargs['queryset'] = Guide.objects.prefetch_related('creator', 'creator__user') \
                .select_related('creator', 'creator__user')

        if db_field.name == 'chapter':
            kwargs['queryset'] = Chapter.objects.prefetch_related('creator', 'creator__user') \
                .select_related('creator', 'creator__user')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator', 'creator__user', 'guide', 'chapter') \
            .select_related('creator', 'creator__user', 'guide', 'chapter')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# ...
# ExplainRevision
# ...
class ExplainRevisionAdmin(admin.ModelAdmin):
    """Extend media admin"""
    model = ExplainRevision
    readonly_fields = ('version', 'uuid',)
    list_display = ('label', 'status', 'version', 'date_created', 'date_updated',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'explain':
            kwargs['queryset'] = Explain.objects.prefetch_related('creator', 'creator__user', 'chapter', 'guide') \
                .select_related('creator', 'creator__user', 'chapter', 'guide')

        if db_field.name == 'content':
            kwargs['queryset'] = Content.objects.prefetch_related('creator', 'creator__user') \
                .select_related('creator', 'creator__user')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator', 'creator__user', 'explain', 'content') \
            .select_related('creator', 'creator__user', 'explain', 'content')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# ...
# REGISTER MODEL
# ...
admin.site.register(Tag)
admin.site.register(Vote)
admin.site.register(Rating)
admin.site.register(Category)
admin.site.register(Attachment)
admin.site.register(Introduction, IntroductionAdmin)
admin.site.register(Guide)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Explain, ExplainAdmin)
admin.site.register(Content)
admin.site.register(GuideRevision, GuideRevisionAdmin)
admin.site.register(ChapterRevision, ChapterRevisionAdmin)
admin.site.register(ExplainRevision, ExplainRevisionAdmin)
