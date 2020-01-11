from django.urls import path, include

from .views import RootApiView

from apps.person.api import routers as person_routers
from apps.beacon.api import routers as beacon_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('person/', include((person_routers, 'person'), namespace='persons')),
    path('beacon/', include((beacon_routers, 'beacon'), namespace='beacons')),
]
