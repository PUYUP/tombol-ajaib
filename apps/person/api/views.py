from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, NotAcceptable

# JWT --> https://github.com/davesque/django-rest-framework-simplejwt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

# SERIALIZERS
from .serializers import (
    PersonSerializer,
    CreateSerializer,
    SingleSerializer
)

# GET MODELS FROM GLOBAL UTILS
from utils.generals import get_model

# LOCAL UTILS
from ..utils.generals import random_string
from ..utils.auths import (
    send_secure_code,
    validate_secure_code,
    get_user_from_email
)

Person = get_model('person', 'Person')


class TokenObtainPairSerializerExtend(TokenObtainPairSerializer):
    """Extend JWT token response"""
    def validate(self, attrs):
        data = super().validate(attrs)
        person = getattr(self.user, 'person', None)

        if person:
            data['uuid'] = person.uuid
            data['username'] = self.user.username
            data['first_name'] = self.user.first_name

        return data


class TokenObtainPairViewExtend(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializerExtend

    @method_decorator(never_cache)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        code = random_string()
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # Save code to localStorage
        serializer.validated_data['auth_code'] = code

        # Prepare Cookie data
        serializer.validated_data[code] = {
            'refresh': serializer.validated_data['refresh'],
            'access': serializer.validated_data['access']
        }

        # Remove token
        serializer.validated_data.pop('refresh')
        serializer.validated_data.pop('access')

        # Make user logged-in
        if settings.SESSION_LOGIN:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class SecureActionApiView(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """
        identifier: identifier secure code use for action?
        {
            "action": "request_secure_code",
            "email": "hellopuyup@gmail.com",
            "identifier": "email"
        }

        {
            "action": "validate_secure_code",
            "secure_code": "KMF9E6EA"
        }
        """
        action = request.data.get('action', None)
        identifier = request.data.get('identifier', None)
        method = request.data.get('method', None)
        email = request.data.get('email', None)
        new_value = request.data.get('new_value', None)

        # For secure code validation
        secure_code = request.data.get('secure_code', None)

        # Get user from default user email if logged in
        if self.request.user.is_authenticated:
            user = self.request.user
            email = getattr(user, 'email', None)
        else:
            user = get_user_from_email(self, email)

        person = getattr(user, 'person', None)

        # Use new email
        if identifier == 'email' and new_value:
            email = new_value

        if not action or not identifier:
            raise NotAcceptable()

        if action == 'request_secure_code':
            secure_data = send_secure_code(
                self, email=email, user=user, new_value=new_value,
                method=method, identifier=identifier)

            if secure_data:
                return Response({'secure_hash': secure_data['secure_hash']},
                                status=status.HTTP_200_OK)
            raise NotFound(detail=_("Email tidak ditemukan."))

        if action == 'validate_secure_code' and secure_code:
            validate = validate_secure_code(self, secure_code=secure_code)
            if validate:
                return Response(status=status.HTTP_200_OK)
            raise NotFound(detail=_("Kode otentikasi salah."))

        raise NotAcceptable()
