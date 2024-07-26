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
        
        customer_data_failed = FailedCustomerData.objects.filter(user=user )
        customer_data_passed = PassedCustomerData.objects.filter(user=user)
        customer_data_repassed = RePassedCustomerData.objects.filter(user=user)

        failed_serializer = FailedCustomerDataSerializer(customer_data_failed, many=True)
        passed_serializer = PassedCustomerDataSerializer(customer_data_passed, many=True)
        repassed_serializer = RePassedCustomerDataSerializer(customer_data_repassed, many=True)

        permission = AuthTokenPermission()
        action = f'User view has been accessed using auth token.'
        user = request.user.username
        permission.get_notify(action,user, 'auth_group')
        return Response({'user':user,'message':'Home view accessed with auth token.','passed_customer_data': passed_serializer.data,'failed_customer_data':failed_serializer.data,'re_passed_customer_data': repassed_serializer.data}, status=status.HTTP_200_OK)

class UserPassedDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            passed_customer_data = PassedCustomerData.objects.get(user=user,pk=pk)
            serializer = PassedCustomerDataSerializer(passed_customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except passed_customer_data.DoesNotExist:
            return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)

class UserFailedDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            failed_customer_data = FailedCustomerData.objects.get(user=user,pk=pk)
            serializer = FailedCustomerDataSerializer(failed_customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except FailedCustomerData.DoesNotExist:
            return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)        
    def post(self, request, pk):
        user = request.user
        print('Hello Failed USer')
        try:
            failed_customer_data = FailedCustomerData.objects.get(user=user,pk=pk)
            failed_customer_data.reason = 'Passed by Rechecking'
            failed_customer_data.verified = True

            failed_serializer = FailedCustomerDataSerializer(failed_customer_data)
            passed_serializer = PassedCustomerDataSerializer(data=failed_serializer.data)
            repassed_serializer = RePassedCustomerDataSerializer(data=failed_serializer.data)

            if passed_serializer.is_valid() and repassed_serializer.is_valid():
                passed_serializer.save()
                repassed_serializer.save()
                failed_customer_data.delete()
                return Response({'message': 'Data updated successfully.', 'Customer Data': passed_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'passed_errors': passed_serializer.errors,'repassed_errors':repassed_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except FailedCustomerData.DoesNotExist:
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
                    type = first_data['type']
                    print('TYpe:',type)
                    chain_task.apply_async((first_data, 0, data_list, accepted_data, rejected_data, user_id,type), queue='queue_1')
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


class CreditCardView(APIView):
    permission_classes = [permissions.IsAuthenticated,JWTTokenPermission]
    

    def get(self, request):
        user = request.user
        print('User',user)
        
        customer_data_failed = CreditCardFailedModel.objects.filter(user=user )
        customer_data_passed = CreditCardPassedModel.objects.filter(user=user)
        customer_data_repassed = CreditRePassedModel.objects.filter(user=user)

        failed_serializer = CreditCardFailedSerializer(customer_data_failed, many=True)
        passed_serializer = CreditCardPassedSerializer(customer_data_passed, many=True)
        repassed_serializer = CreditCardRepassedSerializer(customer_data_repassed, many=True)

        permission = AuthTokenPermission()
        action = f'User view has been accessed using auth token.'
        user = request.user.username
        permission.get_notify(action,user, 'auth_group')
        return Response({'user':user,'message':'Home view accessed with auth token.','credit_passed_customer_data': passed_serializer.data,'credit_failed_customer_data':failed_serializer.data,'credit_re_passed_customer_data': repassed_serializer.data}, status=status.HTTP_200_OK)

class CreditCardPassedDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            passed_customer_data = CreditCardPassedModel.objects.get(user=user,pk=pk)
            serializer = CreditCardPassedSerializer(passed_customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Credit Card Passed Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except passed_customer_data.DoesNotExist:
            return Response({'error': 'Credit Card Customer Data not found'}, status=status.HTTP_404_NOT_FOUND)

class CreditCardFailedDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            failed_customer_data = CreditCardFailedModel.objects.get(user=user,pk=pk)
            serializer = CreditCardFailedSerializer(failed_customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Credit Card Failed Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except CreditCardFailedModel.DoesNotExist:
            return Response({'error': 'Credit Card Failed Customer Data not found'}, status=status.HTTP_404_NOT_FOUND)        
    def post(self, request, pk):
        user = request.user
        print('Hello Failed USer')
        try:
            failed_customer_data = CreditCardFailedModel.objects.get(user=user,pk=pk)
            failed_customer_data.reason = 'Passed by Rechecking'
            failed_customer_data.verified = True

            failed_serializer = CreditCardFailedSerializer(failed_customer_data)
            passed_serializer = CreditCardPassedSerializer(data=failed_serializer.data)
            repassed_serializer = CreditCardRepassedSerializer(data=failed_serializer.data)

            if passed_serializer.is_valid() and repassed_serializer.is_valid():
                passed_serializer.save()
                repassed_serializer.save()
                failed_customer_data.delete()
                return Response({'message': 'Data updated successfully.', 'Credit Card Passed Customer Data': passed_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'credit_card_passed_errors': passed_serializer.errors,'credit_card_repassed_errors':repassed_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except CreditCardFailedModel.DoesNotExist:
            return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)   
        


class EcommerceView(APIView):
    permission_classes = [permissions.IsAuthenticated,JWTTokenPermission]
    

    def get(self, request):
        user = request.user
        print('User',user)
        
        customer_data_failed = ECommerceFailedModel.objects.filter(user=user )
        customer_data_passed = ECommercePassedModel.objects.filter(user=user)
        customer_data_repassed = ECommerceRePassedModel.objects.filter(user=user)

        failed_serializer = EcommerceFailedSerializer(customer_data_failed, many=True)
        passed_serializer = EcommercePassedSerializer(customer_data_passed, many=True)
        repassed_serializer = EcommerceRepassedSerializer(customer_data_repassed, many=True)

        permission = AuthTokenPermission()
        action = f'User view has been accessed using auth token.'
        user = request.user.username
        permission.get_notify(action,user, 'auth_group')
        return Response({'user':user,'message':'Home view accessed with auth token.','ecom_passed_customer_data': passed_serializer.data,'ecom_failed_customer_data':failed_serializer.data,'ecom_re_passed_customer_data': repassed_serializer.data}, status=status.HTTP_200_OK)

class EcommercePassedDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            passed_customer_data = ECommercePassedModel.objects.get(user=user,pk=pk)
            serializer = EcommercePassedSerializer(passed_customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Ecommerce Passed Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except passed_customer_data.DoesNotExist:
            return Response({'error': 'Ecommerce Customer Data not found'}, status=status.HTTP_404_NOT_FOUND)

class EcommerceFailedDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request, pk):
        user = request.user
        try:
            failed_customer_data = ECommerceFailedModel.objects.get(user=user,pk=pk)
            serializer = EcommerceFailedSerializer(failed_customer_data)

            return Response({'message': 'Data retrieved successfully.', 'Ecommerce Failed Customer Data': serializer.data}, status=status.HTTP_200_OK)

        except ECommerceFailedModel.DoesNotExist:
            return Response({'error': 'Credit Card Failed Customer Data not found'}, status=status.HTTP_404_NOT_FOUND)        
    def post(self, request, pk):
        user = request.user
        print('Hello Failed USer')
        try:
            failed_customer_data = ECommerceFailedModel.objects.get(user=user,pk=pk)
            failed_customer_data.reason = 'Passed by Rechecking'
            failed_customer_data.verified = True

            failed_serializer = EcommerceFailedSerializer(failed_customer_data)
            passed_serializer = EcommercePassedSerializer(data=failed_serializer.data)
            repassed_serializer = EcommerceRepassedSerializer(data=failed_serializer.data)

            if passed_serializer.is_valid() and repassed_serializer.is_valid():
                passed_serializer.save()
                repassed_serializer.save()
                failed_customer_data.delete()
                return Response({'message': 'Data updated successfully.', 'Ecommerce Passed Customer Data': passed_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'ecommerce_passed_errors': passed_serializer.errors,'ecommerce_repassed_errors':repassed_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except ECommerceFailedModel.DoesNotExist:
            return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)           
        
from django.db.models import Count

class EmploymentCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
        status_counts = FailedCustomerData.objects.values('employment_status').annotate(count=Count('employment_status'))
        
        result = {item['employment_status']: item['count'] for item in status_counts}
        
        return Response(result)

class AMLEmploymentCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
    
        models = [
            ErrorLogsModel, FailedCustomerData, PassedCustomerData,RePassedCustomerData,
            ECommerceFailedModel,CreditCardFailedModel
        ]
        
        aml_risk_true_counts = {}
        
        for model in models:
            true_counts = model.objects.filter(aml_risk=True).values('employment_status').annotate(count=Count('employment_status'))
            for entry in true_counts:
                status = entry['employment_status']
                count = entry['count']
                if status in aml_risk_true_counts:
                    aml_risk_true_counts[status] += count
                else:
                    aml_risk_true_counts[status] = count
            

        response = aml_risk_true_counts
        
        return Response(response)
    
class FailedLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
        models = [FailedCustomerData,ECommerceFailedModel,CreditCardFailedModel]   
        locations = []

        for model in models:
            datas = model.objects.values('id','latitude','longitude')

            for data in datas:
                locations.append({'latitude':data['latitude'],'longitude':data['longitude'],'id':data['id']})

        return Response(locations)        


class DeviceCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
        status_counts = FailedCustomerData.objects.values('device_os').annotate(count=Count('device_os'))
        
        result = {item['device_os']: item['count'] for item in status_counts}
        
        return Response(result)
    
class AMLDeviceCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
    
        models = [
            ErrorLogsModel, FailedCustomerData, PassedCustomerData,RePassedCustomerData
        ]
        
        aml_risk_true_counts = {}
        
        for model in models:
            true_counts = model.objects.filter(aml_risk=True).values('device_os').annotate(count=Count('device_os'))
            for entry in true_counts:
                status = entry['device_os']
                count = entry['count']
                if status in aml_risk_true_counts:
                    aml_risk_true_counts[status] += count
                else:
                    aml_risk_true_counts[status] = count
            

        response = aml_risk_true_counts
        
        return Response(response)    
    

class FailedLocationAMLView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self, request):
        models = [FailedCustomerData, ECommerceFailedModel, CreditCardFailedModel , PassedCustomerData,ECommercePassedModel,ECommerceRePassedModel,CreditCardPassedModel]
        locations = []

        for model in models:
            datas = model.objects.filter(aml_risk=True).values('id', 'latitude', 'longitude')

            for data in datas:
                locations.append({'latitude': data['latitude'], 'longitude': data['longitude'], 'id': data['id']})

        return Response(locations)    
    

class PaymentTypeCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
        status_counts = FailedCustomerData.objects.values('payment_type').annotate(count=Count('payment_type'))
        
        result = {item['payment_type']: item['count'] for item in status_counts}
        
        return Response(result)
    
class AMLPaymentTypeCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
    
        models = [
            ErrorLogsModel, FailedCustomerData, PassedCustomerData,RePassedCustomerData
        ]
        
        aml_risk_true_counts = {}
        
        for model in models:
            true_counts = model.objects.filter(aml_risk=True).values('payment_type').annotate(count=Count('payment_type'))
            for entry in true_counts:
                status = entry['payment_type']
                count = entry['count']
                if status in aml_risk_true_counts:
                    aml_risk_true_counts[status] += count
                else:
                    aml_risk_true_counts[status] = count
            

        response = aml_risk_true_counts
        
        return Response(response)    
    

class HousingCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
        status_counts = FailedCustomerData.objects.values('housing_status').annotate(count=Count('housing_status'))
        
        result = {item['housing_status']: item['count'] for item in status_counts}
        
        return Response(result)
    
class AMLHousingCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
    
        models = [
            ErrorLogsModel, FailedCustomerData, PassedCustomerData,RePassedCustomerData
        ]
        
        aml_risk_true_counts = {}
        
        for model in models:
            true_counts = model.objects.filter(aml_risk=True).values('housing_status').annotate(count=Count('housing_status'))
            for entry in true_counts:
                status = entry['housing_status']
                count = entry['count']
                if status in aml_risk_true_counts:
                    aml_risk_true_counts[status] += count
                else:
                    aml_risk_true_counts[status] = count
            

        response = aml_risk_true_counts
        
        return Response(response)        
    

class SourceCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
        status_counts = FailedCustomerData.objects.values('source').annotate(count=Count('source'))
        
        result = {item['source']: item['count'] for item in status_counts}
        
        return Response(result)
    
class AMLSourceCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, JWTTokenPermission]

    def get(self,request):
    
        models = [
            ErrorLogsModel, FailedCustomerData, PassedCustomerData,RePassedCustomerData
        ]
        
        aml_risk_true_counts = {}
        
        for model in models:
            true_counts = model.objects.filter(aml_risk=True).values('source').annotate(count=Count('source'))
            for entry in true_counts:
                status = entry['source']
                count = entry['count']
                if status in aml_risk_true_counts:
                    aml_risk_true_counts[status] += count
                else:
                    aml_risk_true_counts[status] = count
            

        response = aml_risk_true_counts
        
        return Response(response)            