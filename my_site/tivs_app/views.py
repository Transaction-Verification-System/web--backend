from django.shortcuts import render
from django.http import JsonResponse
from .serializers import *
from .models import *
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import status,permissions
from rest_framework.authentication import SessionAuthentication,BasicAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import login,logout,authenticate
from rest_framework.decorators import authentication_classes,api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import jwt
from .permissions import AuthTokenPermission,JWTTokenPermission
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from rest_framework.authentication import SessionAuthentication 
from rest_framework import status,permissions
# Create your views here.

def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def refreshToken(request):
    user = request.user
    try:
        token = Token.objects.get(user=user)
        token.delete() 
        new_token = Token.objects.create(user=user) 
    except Token.DoesNotExist:
        return Response({'error': 'Token not found'}, status=404)
    except Exception as e:
        return Response({'error': 'Token Expired login again'}, status=501)



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_201_CREATED,'message':'registered successfully'},status=status.HTTP_201_CREATED)
        return Response({'status':status.HTTP_400_BAD_REQUEST,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        

        if serializer.is_valid():
            user = serializer.check(serializer.validated_data)

            if user:
                refresh = RefreshToken.for_user(user)
                login(request,user)
                token, _ = Token.objects.get_or_create(user=user)


                return Response({'access-token':str(refresh.access_token),'api-token':token.key},status=status.HTTP_200_OK)
            else:
                return Response({'errors':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)
        return Response({'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)

  
class LogoutView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request):
        token = Token.objects.get(user=request.user)
        token.delete()
        logout(request)

        return Response({'status':status.HTTP_200_OK,'message':'Logged Out Successfully'},status=status.HTTP_200_OK)
    
def chat_view(request):
    return render(request, 'tivs_app/index.html')    

class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated,AuthTokenPermission]

    def get(self, request):
        permission = AuthTokenPermission()
        action = f'User view has been accessed using auth token.'
        user = request.user.username
        permission.get_notify(action,user, 'auth_group')
        serializer = UserSerializer(request.user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)


class TransactionView(APIView):
    permission_classes = [permissions.IsAuthenticated,JWTTokenPermission]

    def get(self,request):
        permission = JWTTokenPermission()
        action = f'Transaction view has been accessed using jwt token.'
        user = request.user.username
        permission.get_notify(action,user, 'auth_group')
        return Response({'message':'Transaction View'})


