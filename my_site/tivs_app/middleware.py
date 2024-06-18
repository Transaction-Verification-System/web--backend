from django.utils.deprecation import MiddlewareMixin
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.request import Request
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from functools import wraps
from django.http import JsonResponse


User = get_user_model()

# def token_required(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         token = request.headers.get('Authorization')
#         print('Token:', token) 
#         if not token:
#             return JsonResponse({'error': 'Unauthorized access'}, status=401)

#         return view_func(request, *args, **kwargs)

#     return _wrapped_view

# def token_required(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         token = request.headers.get('Authorization')
#         if not token or not token.startswith('Bearer '):
#             return JsonResponse({'error': 'Unauthorized access'}, status=401)

#         # Additional token validation logic can be added here if needed

#         return view_func(request, *args, **kwargs)

#     return _wrapped_view