from rest_framework.permissions import BasePermission
from rest_framework.authtoken.models import Token
import jwt
from django.conf import settings
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

class AuthTokenPermission(BasePermission):
    def has_permission(self, request, view):
        auth_token = request.headers.get('Authorization')
        token = Token.objects.get(user=request.user)

        if auth_token==token.key:
            return True
        else:    
            return False

class JWTTokenPermission(BasePermission):
    def has_permission(self, request, view):
        jwt_token = request.headers.get('Authorization')
        print('JWT Token: ', jwt_token)
        if jwt_token:
            try:
                jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=['HS256'])
                return True
            except (ExpiredSignatureError, InvalidTokenError):
                return False
        return False
