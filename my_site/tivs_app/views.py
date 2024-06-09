from django.shortcuts import render
from django.http import JsonResponse
from .serializers import *
from .models import *
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import status,permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import login,logout,authenticate
from rest_framework.decorators import authentication_classes,api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


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
        token.delete()  # Delete the existing token
        new_token = Token.objects.create(user=user)  # Create a new token for the user
        return Response({'token': new_token.key, 'business': user.is_business}, status=200)
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
            return Response({'status':status.HTTP_201_CREATED,'message':'registered successfully'})
        return Response({'status':status.HTTP_400_BAD_REQUEST,'errors':serializer.errors})

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        

        if serializer.is_valid():
            user = serializer.check(serializer.validated_data)

            if user:
                refresh = RefreshToken.for_user(user)
                login(request,user)
                token, _ = Token.objects.get_or_create(user=user)

                return Response({'refresh':str(refresh),'refresh-token':str(refresh.access_token),'api-token':token.key},status=status.HTTP_200_OK)
            else:
                return Response({'errors':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)
        return Response({'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)

  
class LogoutView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    authentication_classes=[SessionAuthentication]
    def post(self,request):
        token = Token.objects.get(user=request.user)
        token.delete()
        logout(request)

        return Response({'status':status.HTTP_200_OK,'message':'Logged Out Successfully'})

    
class UserView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self,request):
        serializer = UserSerializer(request.user)
        return Response({'user':serializer.data},status=status.HTTP_200_OK)     
    




