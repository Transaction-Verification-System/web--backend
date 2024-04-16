from django.shortcuts import render
from .serializers import *
from .models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status,permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import login,logout,authenticate

# Create your views here.



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        serializer = UserRegisterSerializer(request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':status.HTTP_201_CREATED,'serializer':serializer.data})
        return Response({'status':status.HTTP_400_BAD_REQUEST,'errors':serializer.errors})

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        serializer = UserLoginSerializer(request.data)

        if serializer.is_valid():
            user = serializer.check(serializer.validated_data)

            if user:
                login(request,user)
                token,_ = Token.objects.get_or_create(user=user)

                return Response({'user':user.username,'token':token.key},status=status.HTTP_200_OK)
            return Response({'errors':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)
        return Response({'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    

class LogoutView(APIView):
    def post(self,request):
        logout(request)

        return Response({'status':status.HTTP_200_OK,'message':'Logged Out Successfully'})
    
class UserView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self,request):
        serializer = UserSerializer(request.user)
        return Response({'user':serializer.data},status=status.HTTP_200_OK)     
    





