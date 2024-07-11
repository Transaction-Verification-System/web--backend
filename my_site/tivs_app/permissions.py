from rest_framework.permissions import BasePermission
from rest_framework.authtoken.models import Token
import jwt
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError



def ready_message(action,user):
    return {
        'user':user,
        'message':action
    }


class AuthTokenPermission(BasePermission):
    def has_permission(self, request, view):
        print('Hello permission')
        auth_token = request.headers.get('Authorization')
        token = Token.objects.get(user=request.user)

        if auth_token==token.key:
            return True
        else:    
            return False
    def get_notify(self,action,user,group_name):
        message = ready_message(action,user)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
           group_name,
            {
                'type':'send_message',
                'message': message
            }
        )    

class JWTTokenPermission(BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')
        print('Authorization Header:', auth_header)
        if auth_header:
            try:
                if auth_header.startswith('Bearer '):
                    print('Yes')
                    jwt_token = auth_header.split(' ')[1]
                    print('JWT Token:', jwt_token)
                    jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=['HS256'])
                    return True
            except (ExpiredSignatureError, InvalidTokenError) as e:
                print('JWT Token error:', str(e))
                return False
        return False
    
    def get_notify(self, action, user, group_name):
        message = ready_message(action, user)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_message',
                'message': message
            }
        )
