from django.utils.deprecation import MiddlewareMixin
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.request import Request
from .views import verify_token
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED


User = get_user_model()

class TokenAuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        token_key = request.headers.get('Authorization')
        print('Token Key:',token_key)
        channel_layer = get_channel_layer()

        if token_key:
            token_key = token_key.split()[1]
            try:
                token = Token.objects.get(key=token_key)
                print('Token:',token.user)
                request.user = token.user
                request.is_token_valid = True
                # if channel_layer is not None:
                async_to_sync(channel_layer.group_send)(
                    'chat_group', 
                    {
                        'type': 'chat.message',
                        'message': 'API token detected, data ready!'
                    }
                )
            except Token.DoesNotExist:
                request.user = AnonymousUser()
                request.is_token_valid = False
        else:
            request.user = AnonymousUser()
            request.is_token_valid = False
