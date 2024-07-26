from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model,authenticate
from rest_framework.exceptions import ValidationError

User_Model = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Model
        fields='__all__'

    def create(self,clean_data):
        user_obj = User_Model.objects.create_user(email=clean_data['email'],username=clean_data['username'],password=clean_data['password'])
        user_obj.save()
        return user_obj

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


    def check(self,validated_data):
        user = authenticate(email = validated_data['email'],password = validated_data['password'])
        if not user:
            raise ValidationError('User not found.')
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Model
        fields = ['email','username']    

class BlackListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackListModel
        fields = '__all__'

class PassedCustomerDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassedCustomerData
        fields = '__all__'

class FailedCustomerDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailedCustomerData
        fields = '__all__'        

class RePassedCustomerDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RePassedCustomerData
        fields = '__all__'      


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorLogsModel
        fields = '__all__'


class CreditCardPassedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCardPassedModel
        fields = '__all__'


class CreditCardFailedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCardFailedModel
        fields = '__all__'


class CreditCardRepassedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRePassedModel
        fields = '__all__'


class CreditCardErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCardErrorLogModel
        fields = '__all__'


class EcommercePassedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ECommercePassedModel
        fields = '__all__'
    def to_internal_value(self, data):
        # Map incoming data fields to the model fields
        internal_data = {
            'user':data.get('user'),
            'no_transactions': data.get('No_Transactions'),
            'no_orders': data.get('No_Orders'),
            'no_payments': data.get('No_Payments'),
            'total_transaction_amt': data.get('Total_transaction_amt'),
            'no_transactions_fail': data.get('No_transactionsFail'),
            'payment_reg_fail': data.get('PaymentRegFail'),
            'paypal_payments': data.get('PaypalPayments'),
            'apple_payments': data.get('ApplePayments'),
            'card_payments': data.get('CardPayments'),
            'bitcoin_payments': data.get('BitcoinPayments'),
            'orders_fulfilled': data.get('OrdersFulfilled'),
            'orders_pending': data.get('OrdersPending'),
            'orders_failed': data.get('OrdersFailed'),
            'trns_fail_order_fulfilled': data.get('Trns_fail_order_fulfilled'),
            'duplicate_ip': data.get('Duplicate_IP'),
            'duplicate_address': data.get('Duplicate_Address'),
            'jcb_16': data.get('JCB_16'),
            'american_exp': data.get('AmericanExp'),
            'visa_16': data.get('VISA_16'),
            'discover': data.get('Discover'),
            'voyager': data.get('Voyager'),
            'visa_13': data.get('VISA_13'),
            'maestro': data.get('Maestro'),
            'mastercard': data.get('Mastercard'),
            'dc_cb': data.get('DC_CB'),
            'jcb_15': data.get('JCB_15'),
            'phone': data.get('phone'),
            'reason': data.get('reason'),
            'verified': data.get('verified', False)  # Default to False if not provided
        }
        return super().to_internal_value(internal_data)    


class EcommerceFailedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ECommerceFailedModel
        fields = '__all__'

    def to_internal_value(self, data):
        internal_data = {
            'user':data.get('user'),
            'no_transactions': data.get('No_Transactions'),
            'no_orders': data.get('No_Orders'),
            'no_payments': data.get('No_Payments'),
            'total_transaction_amt': data.get('Total_transaction_amt'),
            'no_transactions_fail': data.get('No_transactionsFail'),
            'payment_reg_fail': data.get('PaymentRegFail'),
            'paypal_payments': data.get('PaypalPayments'),
            'apple_payments': data.get('ApplePayments'),
            'card_payments': data.get('CardPayments'),
            'bitcoin_payments': data.get('BitcoinPayments'),
            'orders_fulfilled': data.get('OrdersFulfilled'),
            'orders_pending': data.get('OrdersPending'),
            'orders_failed': data.get('OrdersFailed'),
            'trns_fail_order_fulfilled': data.get('Trns_fail_order_fulfilled'),
            'duplicate_ip': data.get('Duplicate_IP'),
            'duplicate_address': data.get('Duplicate_Address'),
            'jcb_16': data.get('JCB_16'),
            'american_exp': data.get('AmericanExp'),
            'visa_16': data.get('VISA_16'),
            'discover': data.get('Discover'),
            'voyager': data.get('Voyager'),
            'visa_13': data.get('VISA_13'),
            'maestro': data.get('Maestro'),
            'mastercard': data.get('Mastercard'),
            'dc_cb': data.get('DC_CB'),
            'jcb_15': data.get('JCB_15'),
            'phone': data.get('phone'),
            'reason': data.get('reason'),
            'verified': data.get('verified', False) 
        }

        
        return super().to_internal_value(internal_data)


class EcommerceRepassedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ECommerceRePassedModel
        fields = '__all__'

    def to_internal_value(self, data):
        internal_data = {
            'user':data.get('user'),
            'no_transactions': data.get('No_Transactions'),
            'no_orders': data.get('No_Orders'),
            'no_payments': data.get('No_Payments'),
            'total_transaction_amt': data.get('Total_transaction_amt'),
            'no_transactions_fail': data.get('No_transactionsFail'),
            'payment_reg_fail': data.get('PaymentRegFail'),
            'paypal_payments': data.get('PaypalPayments'),
            'apple_payments': data.get('ApplePayments'),
            'card_payments': data.get('CardPayments'),
            'bitcoin_payments': data.get('BitcoinPayments'),
            'orders_fulfilled': data.get('OrdersFulfilled'),
            'orders_pending': data.get('OrdersPending'),
            'orders_failed': data.get('OrdersFailed'),
            'trns_fail_order_fulfilled': data.get('Trns_fail_order_fulfilled'),
            'duplicate_ip': data.get('Duplicate_IP'),
            'duplicate_address': data.get('Duplicate_Address'),
            'jcb_16': data.get('JCB_16'),
            'american_exp': data.get('AmericanExp'),
            'visa_16': data.get('VISA_16'),
            'discover': data.get('Discover'),
            'voyager': data.get('Voyager'),
            'visa_13': data.get('VISA_13'),
            'maestro': data.get('Maestro'),
            'mastercard': data.get('Mastercard'),
            'dc_cb': data.get('DC_CB'),
            'jcb_15': data.get('JCB_15'),
            'phone': data.get('phone'),
            'reason': data.get('reason'),
            'verified': data.get('verified', False)  # Default to False if not provided
        }

        
        return super().to_internal_value(internal_data)    


class EcommerceErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ECommerceErrorModel
        fields = '__all__'


    def to_internal_value(self, data):
        # Map incoming data fields to the model fields
        internal_data = {
            'user':data.get('user'),
            'no_transactions': data.get('No_Transactions'),
            'no_orders': data.get('No_Orders'),
            'no_payments': data.get('No_Payments'),
            'total_transaction_amt': data.get('Total_transaction_amt'),
            'no_transactions_fail': data.get('No_transactionsFail'),
            'payment_reg_fail': data.get('PaymentRegFail'),
            'paypal_payments': data.get('PaypalPayments'),
            'apple_payments': data.get('ApplePayments'),
            'card_payments': data.get('CardPayments'),
            'bitcoin_payments': data.get('BitcoinPayments'),
            'orders_fulfilled': data.get('OrdersFulfilled'),
            'orders_pending': data.get('OrdersPending'),
            'orders_failed': data.get('OrdersFailed'),
            'trns_fail_order_fulfilled': data.get('Trns_fail_order_fulfilled'),
            'duplicate_ip': data.get('Duplicate_IP'),
            'duplicate_address': data.get('Duplicate_Address'),
            'jcb_16': data.get('JCB_16'),
            'american_exp': data.get('AmericanExp'),
            'visa_16': data.get('VISA_16'),
            'discover': data.get('Discover'),
            'voyager': data.get('Voyager'),
            'visa_13': data.get('VISA_13'),
            'maestro': data.get('Maestro'),
            'mastercard': data.get('Mastercard'),
            'dc_cb': data.get('DC_CB'),
            'jcb_15': data.get('JCB_15'),
            'phone': data.get('phone'),
            'reason': data.get('reason'),
            'verified': data.get('verified', False)  # Default to False if not provided
        }
        
        return super().to_internal_value(internal_data)    
