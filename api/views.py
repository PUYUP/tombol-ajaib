# THIRD PARTY
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'user': {
                'persons': reverse('persons:person:person-list', request=request,
                                   format=format, current_app='person'),
                'attributes': reverse('persons:person:attribute-list', request=request,
                                      format=format, current_app='person'),
                'validations': reverse('persons:person:validation-list', request=request,
                                       format=format, current_app='person'),
            },
            'beacon': {
                'guides': reverse('beacons:beacon:guide-list', request=request,
                                  format=format, current_app='beacon'),
                'guides-revisions': reverse('beacons:beacon:guide_revision-list',
                                            request=request, format=format,
                                            current_app='beacon'),
                'introductions': reverse('beacons:beacon:introduction-list',
                                         request=request, format=format,
                                         current_app='beacon'),
                'chapters': reverse('beacons:beacon:chapter-list',
                                    request=request, format=format,
                                    current_app='beacon'),
                'chapters-revisions': reverse('beacons:beacon:chapter_revision-list',
                                              request=request, format=format,
                                              current_app='beacon'),
                'explains': reverse('beacons:beacon:explain-list',
                                    request=request, format=format,
                                    current_app='beacon'),
                'explains-revisions': reverse('beacons:beacon:explain_revision-list',
                                              request=request, format=format,
                                              current_app='beacon'),
            },
        })
