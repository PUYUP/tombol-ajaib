from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# URL's
from api import routers as api_routers
from public import urls as core_urls

from apps.person.public import urls as person_urls
from apps.beacon.public.guide import urls as guide_urls
from apps.beacon.public.chapter import urls as chapter_urls
from apps.beacon.public.explain import urls as explain_urls

urlpatterns = [
    path('', include(core_urls)),
    path('api/', include(api_routers)),
    path('person/', include(person_urls)),
    path('guide/', include(guide_urls)),
    path('explain/', include(explain_urls)),
    path('chapter/', include(chapter_urls)),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    