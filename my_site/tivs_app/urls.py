from django.urls import path
from .views import *

urlpatterns = [
    path('register/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('history/',UserView.as_view(),name='session'),
    path('transaction/',TransactionView.as_view(),name='transaction'),
    path('csrf/',get_csrf_token,name='csrf_token'),
    path('text/', chat_view, name='chat'),
    path('task/',queue_result, name='queue'),
    path('success/',sucess,name='success'),
    path('passed/detail/<int:pk>/',UserPassedDetailView.as_view(),name='user_detail'),
    path('failed/detail/<int:pk>/',UserFailedDetailView.as_view(),name='user_detail'),

    path('credit/',CreditCardView.as_view(),name='credit_view'),
    path('credit/passed/detail/<int:pk>/',CreditCardPassedDetailView.as_view(),name='credit_passed_detail'),
    path('credit/failed/detail/<int:pk>/',CreditCardFailedDetailView.as_view(),name='credit_failed_detail'),

    path('ecom/',EcommerceView.as_view(),name='ecom'),
    path('ecom/passed/detail/<int:pk>/',EcommercePassedDetailView.as_view(),name='ecom_passed_detail'),
    path('ecom/failed/detail/<int:pk>/',EcommerceFailedDetailView.as_view(),name='ecom_failed_detail'),

    path('insights/fraud/employment/',EmploymentCountView.as_view(),name='employ_count'),
    path('insights/aml/employment/',AMLEmploymentCountView.as_view(),name='aml_emp_count'),

    path('insights/fraud/location/',FailedLocationView.as_view(),name='failed_location'),
    path('insights/aml/location/',FailedLocationAMLView.as_view(),name='aml_location_count'),

    path('insights/fraud/device/',DeviceCountView.as_view(),name='failed_device'),
    path('insights/aml/device/',AMLDeviceCountView.as_view(),name='aml_device_count'),

    path('insights/fraud/payment/',PaymentTypeCountView.as_view(),name='payment_device'),
    path('insights/aml/payment/',AMLPaymentTypeCountView.as_view(),name='aml_payment_count'),

    path('insights/fraud/housing/',HousingCountView.as_view(),name='housing_device'),
    path('insights/aml/housing/',AMLHousingCountView.as_view(),name='aml_housing_count'),

]


