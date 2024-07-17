from django.shortcuts import render,redirect
from django.http import JsonResponse
from .serializers import *
from .models import *
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
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
from .tasks import chain_task,chain_task2
from django.views.decorators.csrf import csrf_exempt,csrf_protect,ensure_csrf_cookie

from django.utils.decorators import method_decorator
import logging
from celery import Celery

app = Celery('my_site')
logger = logging.getLogger(__name__)

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
    permission_classes=[permissions.IsAuthenticated,JWTTokenPermission]
    def post(self,request):
        token = Token.objects.get(user=request.user)
        token.delete()
        logout(request)

        return Response({'status':status.HTTP_200_OK,'message':'Logged Out Successfully'},status=status.HTTP_200_OK)
    
def chat_view(request):
    return render(request, 'tivs_app/index.html')    

class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated,JWTTokenPermission]
    

    def get(self, request):
        user = request.user
        print('User',user)
        
        customer_data_failed = CustomerData.objects.filter(user=user ,verified = False)
        customer_data_passed = CustomerData.objects.filter(user=user,verified = True)

        failed_serializer = CustomerDataSerializer(customer_data_failed, many=True)
        passed_serializer = CustomerDataSerializer(customer_data_passed, many=True)

        permission = AuthTokenPermission()
        action = f'User view has been accessed using auth token.'
        user = request.user.username
        permission.get_notify(action,user, 'auth_group')
        return Response({'user':user,'message':'Home view accessed with auth token.','passed_customer_data': passed_serializer.data,'failed_customer_data':failed_serializer.data}, status=status.HTTP_200_OK)

class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            customer_data = CustomerData.objects.get(user=user,pk=pk)
            serializer = CustomerDataSerializer(customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except CustomerData.DoesNotExist:
            return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)
        
class TransactionView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(TransactionView, self).dispatch(*args, **kwargs)

    @method_decorator(ensure_csrf_cookie)
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            data_list = request.data
            accepted_data = 0
            rejected_data = 0
            user_id = request.user.id
            logger.info(f'Initial Accepted data: {accepted_data}, Initial Rejected data: {rejected_data}')
            logger.info(f'User ID: {user_id}')
            logger.info(f'Data List: {data_list}')
            print(f'Initial Accepted data: {accepted_data}, Initial Rejected data: {rejected_data}')
            print(f'User ID: {user_id}')
            print(f'Data List: {data_list}')
            try:
                if data_list:
                    first_data = data_list[0]
                    chain_task.apply_async((first_data, 0, data_list, accepted_data, rejected_data, user_id), queue='queue_1')
                else:
                    raise ValueError('Empty data_list provided')
                return redirect('success')  
            except (KeyError, ValueError) as e:
                return Response({'error': str(e)}, status=400)
            except Exception as e:
                return Response({'error': str(e)}, status=500)
        return render(request, 'tivs_app/index.html')

      

    def get(self,request):
        permission = JWTTokenPermission()
        action = f'Transaction view has been accessed using jwt token.'
        user = request.user.username
        print('User:',user)
        permission.get_notify(action,user, 'auth_group')
        return Response({'message':'Transaction View'})


from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from celery import chain

@csrf_exempt
def queue_result(request):
    if request.method == 'POST':
        num1 = int(request.POST['number1'])
        num2 = int(request.POST['number2'])

        chain_task.apply_async((num1,num2),queue='queue_1')

        return redirect('success')

    return render(request,'tivs_app/index.html')

def sucess(request):
    return render(request, 'tivs_app/success.html')