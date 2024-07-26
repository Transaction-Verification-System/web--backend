from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,BaseUserManager,User
from django.conf import settings


# Create your models here.

class AppUserManager(BaseUserManager):
    def create_user(self,email,username,password=None):
        if not email:
            raise ValueError('Please enter Email.')
        if not password:
            raise ValueError('Please enter Password!')
        
        email = self.normalize_email(email)
        user = self.model(email=email,username=username)
        user.set_password(password)
        user.save()

        return user
    
    def create_superuser(self,email,username,password=None):
        if not email:
            raise ValueError('Please enter Email.')
        if not password:
            raise ValueError('Please enter password!')

        user = self.create_user(email,username,password)
        user.is_superuser = True
        user.save()

        return user
    
class AppUser(AbstractBaseUser,PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254,unique=True)
    username = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)


    USERNAME_FIELD='email'
    REQUIRED_FIELDS =['username']
    
    objects=AppUserManager()

    def __str__(self):
        return self.username


class BlackListModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.phone

class PassedCustomerData(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    income = models.FloatField()
    name_email_similarity = models.FloatField()
    prev_address_months_count = models.IntegerField()
    current_address_months_count = models.IntegerField()
    customer_age = models.IntegerField()
    days_since_request = models.FloatField()
    intended_balcon_amount = models.FloatField()
    payment_type = models.CharField(max_length=255)
    zip_count_4w = models.IntegerField()
    velocity_6h = models.FloatField()
    velocity_24h = models.FloatField()
    velocity_4w = models.FloatField()
    bank_branch_count_8w = models.IntegerField()
    date_of_birth_distinct_emails_4w = models.IntegerField()
    employment_status = models.CharField(max_length=255)
    credit_risk_score = models.IntegerField()
    email_is_free = models.IntegerField()
    housing_status = models.CharField(max_length=255)
    phone_home_valid = models.IntegerField()
    phone_mobile_valid = models.IntegerField()
    bank_months_count = models.IntegerField()
    has_other_cards = models.IntegerField()
    proposed_credit_limit = models.FloatField()
    foreign_request = models.IntegerField()
    source = models.CharField(max_length=255)
    session_length_in_minutes = models.FloatField()
    device_os = models.CharField(max_length=255)
    keep_alive_session = models.IntegerField()
    device_distinct_emails_8w = models.IntegerField()
    device_fraud_count = models.IntegerField()
    month = models.IntegerField()
    phone = models.CharField(max_length=15)
    verified = models.BooleanField()
    reason = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    aml_risk = models.BooleanField(default=False, blank=True) 


    def __str__(self):
        return f"Passed Customer Data: {self.id}"

class FailedCustomerData(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    income = models.FloatField()
    name_email_similarity = models.FloatField()
    prev_address_months_count = models.IntegerField()
    current_address_months_count = models.IntegerField()
    customer_age = models.IntegerField()
    days_since_request = models.FloatField()
    intended_balcon_amount = models.FloatField()
    payment_type = models.CharField(max_length=255)
    zip_count_4w = models.IntegerField()
    velocity_6h = models.FloatField()
    velocity_24h = models.FloatField()
    velocity_4w = models.FloatField()
    bank_branch_count_8w = models.IntegerField()
    date_of_birth_distinct_emails_4w = models.IntegerField()
    employment_status = models.CharField(max_length=255)
    credit_risk_score = models.IntegerField()
    email_is_free = models.IntegerField()
    housing_status = models.CharField(max_length=255)
    phone_home_valid = models.IntegerField()
    phone_mobile_valid = models.IntegerField()
    bank_months_count = models.IntegerField()
    has_other_cards = models.IntegerField()
    proposed_credit_limit = models.FloatField()
    foreign_request = models.IntegerField()
    source = models.CharField(max_length=255)
    session_length_in_minutes = models.FloatField()
    device_os = models.CharField(max_length=255)
    keep_alive_session = models.IntegerField()
    device_distinct_emails_8w = models.IntegerField()
    device_fraud_count = models.IntegerField()
    month = models.IntegerField()
    phone = models.CharField(max_length=15)
    verified = models.BooleanField()
    reason = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    aml_risk = models.BooleanField(default=False, blank=True)  



    def __str__(self):
        return f"Failed Customer Data: {self.id}"    
    
class RePassedCustomerData(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    income = models.FloatField()
    name_email_similarity = models.FloatField()
    prev_address_months_count = models.IntegerField()
    current_address_months_count = models.IntegerField()
    customer_age = models.IntegerField()
    days_since_request = models.FloatField()
    intended_balcon_amount = models.FloatField()
    payment_type = models.CharField(max_length=255)
    zip_count_4w = models.IntegerField()
    velocity_6h = models.FloatField()
    velocity_24h = models.FloatField()
    velocity_4w = models.FloatField()
    bank_branch_count_8w = models.IntegerField()
    date_of_birth_distinct_emails_4w = models.IntegerField()
    employment_status = models.CharField(max_length=255)
    credit_risk_score = models.IntegerField()
    email_is_free = models.IntegerField()
    housing_status = models.CharField(max_length=255)
    phone_home_valid = models.IntegerField()
    phone_mobile_valid = models.IntegerField()
    bank_months_count = models.IntegerField()
    has_other_cards = models.IntegerField()
    proposed_credit_limit = models.FloatField()
    foreign_request = models.IntegerField()
    source = models.CharField(max_length=255)
    session_length_in_minutes = models.FloatField()
    device_os = models.CharField(max_length=255)
    keep_alive_session = models.IntegerField()
    device_distinct_emails_8w = models.IntegerField()
    device_fraud_count = models.IntegerField()
    month = models.IntegerField()
    phone = models.CharField(max_length=15)
    verified = models.BooleanField()
    reason = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    aml_risk = models.BooleanField(default=False, blank=True)  


    def __str__(self):
        return f"Re-passed Customer Data: {self.id}"      

class ErrorLogsModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    income = models.FloatField()
    name_email_similarity = models.FloatField()
    prev_address_months_count = models.IntegerField()
    current_address_months_count = models.IntegerField()
    customer_age = models.IntegerField()
    days_since_request = models.FloatField()
    intended_balcon_amount = models.FloatField()
    payment_type = models.CharField(max_length=255)
    zip_count_4w = models.IntegerField()
    velocity_6h = models.FloatField()
    velocity_24h = models.FloatField()
    velocity_4w = models.FloatField()
    bank_branch_count_8w = models.IntegerField()
    date_of_birth_distinct_emails_4w = models.IntegerField()
    employment_status = models.CharField(max_length=255)
    credit_risk_score = models.IntegerField()
    email_is_free = models.IntegerField()
    housing_status = models.CharField(max_length=255)
    phone_home_valid = models.IntegerField()
    phone_mobile_valid = models.IntegerField()
    bank_months_count = models.IntegerField()
    has_other_cards = models.IntegerField()
    proposed_credit_limit = models.FloatField()
    foreign_request = models.IntegerField()
    source = models.CharField(max_length=255)
    session_length_in_minutes = models.FloatField()
    device_os = models.CharField(max_length=255)
    keep_alive_session = models.IntegerField()
    device_distinct_emails_8w = models.IntegerField()
    device_fraud_count = models.IntegerField()
    month = models.IntegerField()
    phone = models.CharField(max_length=15)
    verified = models.BooleanField()
    reason = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    aml_risk = models.BooleanField(default=False, blank=True) 

    def __str__(self):
        return f"Error Customer Data: {self.id}"
    

class CreditCardPassedModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    time = models.FloatField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    v1 = models.FloatField()
    v2 = models.FloatField()
    v3 = models.FloatField()
    v4 = models.FloatField()
    v5 = models.FloatField()
    v6 = models.FloatField()
    v7 = models.FloatField()
    v8 = models.FloatField()
    v9 = models.FloatField()
    v10 = models.FloatField()
    v11 = models.FloatField()
    v12 = models.FloatField()
    v13 = models.FloatField()
    v14 = models.FloatField()
    v15 = models.FloatField()
    v16 = models.FloatField()
    v17 = models.FloatField()
    v18 = models.FloatField()
    v19 = models.FloatField()
    v20 = models.FloatField()
    v21 = models.FloatField()
    v22 = models.FloatField()
    v23 = models.FloatField()
    v24 = models.FloatField()
    v25 = models.FloatField()
    v26 = models.FloatField()
    v27 = models.FloatField()
    v28 = models.FloatField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()


    def __str__(self):
        return f"Credit Passed {self.id}: {self.amount} at {self.time}"    
    
class CreditCardFailedModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    time = models.FloatField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    v1 = models.FloatField()
    v2 = models.FloatField()
    v3 = models.FloatField()
    v4 = models.FloatField()
    v5 = models.FloatField()
    v6 = models.FloatField()
    v7 = models.FloatField()
    v8 = models.FloatField()
    v9 = models.FloatField()
    v10 = models.FloatField()
    v11 = models.FloatField()
    v12 = models.FloatField()
    v13 = models.FloatField()
    v14 = models.FloatField()
    v15 = models.FloatField()
    v16 = models.FloatField()
    v17 = models.FloatField()
    v18 = models.FloatField()
    v19 = models.FloatField()
    v20 = models.FloatField()
    v21 = models.FloatField()
    v22 = models.FloatField()
    v23 = models.FloatField()
    v24 = models.FloatField()
    v25 = models.FloatField()
    v26 = models.FloatField()
    v27 = models.FloatField()
    v28 = models.FloatField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()



    def __str__(self):
        return f"Credit Card Failed {self.id}: {self.amount} at {self.time}"      
    

class CreditRePassedModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    time = models.FloatField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    v1 = models.FloatField()
    v2 = models.FloatField()
    v3 = models.FloatField()
    v4 = models.FloatField()
    v5 = models.FloatField()
    v6 = models.FloatField()
    v7 = models.FloatField()
    v8 = models.FloatField()
    v9 = models.FloatField()
    v10 = models.FloatField()
    v11 = models.FloatField()
    v12 = models.FloatField()
    v13 = models.FloatField()
    v14 = models.FloatField()
    v15 = models.FloatField()
    v16 = models.FloatField()
    v17 = models.FloatField()
    v18 = models.FloatField()
    v19 = models.FloatField()
    v20 = models.FloatField()
    v21 = models.FloatField()
    v22 = models.FloatField()
    v23 = models.FloatField()
    v24 = models.FloatField()
    v25 = models.FloatField()
    v26 = models.FloatField()
    v27 = models.FloatField()
    v28 = models.FloatField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()



    def __str__(self):
        return f"Credit Card Repassed {self.id}: {self.amount} at {self.time}"      
    
class CreditCardErrorLogModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    time = models.FloatField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    v1 = models.FloatField()
    v2 = models.FloatField()
    v3 = models.FloatField()
    v4 = models.FloatField()
    v5 = models.FloatField()
    v6 = models.FloatField()
    v7 = models.FloatField()
    v8 = models.FloatField()
    v9 = models.FloatField()
    v10 = models.FloatField()
    v11 = models.FloatField()
    v12 = models.FloatField()
    v13 = models.FloatField()
    v14 = models.FloatField()
    v15 = models.FloatField()
    v16 = models.FloatField()
    v17 = models.FloatField()
    v18 = models.FloatField()
    v19 = models.FloatField()
    v20 = models.FloatField()
    v21 = models.FloatField()
    v22 = models.FloatField()
    v23 = models.FloatField()
    v24 = models.FloatField()
    v25 = models.FloatField()
    v26 = models.FloatField()
    v27 = models.FloatField()
    v28 = models.FloatField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()



    def __str__(self):
        return f"Credit Card Error {self.id}: {self.amount} at {self.time}"      


class ECommercePassedModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    no_transactions = models.IntegerField()
    no_orders = models.IntegerField()
    no_payments = models.IntegerField()
    total_transaction_amt = models.DecimalField(max_digits=10, decimal_places=2)
    no_transactions_fail = models.IntegerField()
    payment_reg_fail = models.IntegerField()
    paypal_payments = models.IntegerField()
    apple_payments = models.IntegerField()
    card_payments = models.IntegerField()
    bitcoin_payments = models.IntegerField()
    orders_fulfilled = models.IntegerField()
    orders_pending = models.IntegerField()
    orders_failed = models.IntegerField()
    trns_fail_order_fulfilled = models.IntegerField()
    duplicate_ip = models.IntegerField()
    duplicate_address = models.IntegerField()
    jcb_16 = models.IntegerField()
    american_exp = models.IntegerField()
    visa_16 = models.IntegerField()
    discover = models.IntegerField()
    voyager = models.IntegerField()
    visa_13 = models.IntegerField()
    maestro = models.IntegerField()
    mastercard = models.IntegerField()
    dc_cb = models.IntegerField()
    jcb_15 = models.IntegerField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()

    def __str__(self):
        return f"Ecommerce Passed: {self.id}: {self.total_transaction_amt} total amount"        


class ECommerceFailedModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    no_transactions = models.IntegerField()
    no_orders = models.IntegerField()
    no_payments = models.IntegerField()
    total_transaction_amt = models.DecimalField(max_digits=10, decimal_places=2)
    no_transactions_fail = models.IntegerField()
    payment_reg_fail = models.IntegerField()
    paypal_payments = models.IntegerField()
    apple_payments = models.IntegerField()
    card_payments = models.IntegerField()
    bitcoin_payments = models.IntegerField()
    orders_fulfilled = models.IntegerField()
    orders_pending = models.IntegerField()
    orders_failed = models.IntegerField()
    trns_fail_order_fulfilled = models.IntegerField()
    duplicate_ip = models.IntegerField()
    duplicate_address = models.IntegerField()
    jcb_16 = models.IntegerField()
    american_exp = models.IntegerField()
    visa_16 = models.IntegerField()
    discover = models.IntegerField()
    voyager = models.IntegerField()
    visa_13 = models.IntegerField()
    maestro = models.IntegerField()
    mastercard = models.IntegerField()
    dc_cb = models.IntegerField()
    jcb_15 = models.IntegerField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()

    def __str__(self):
        return f"Ecommerce Failed: {self.id}: {self.total_transaction_amt} total amount"  
    

class ECommerceRePassedModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    no_transactions = models.IntegerField()
    no_orders = models.IntegerField()
    no_payments = models.IntegerField()
    total_transaction_amt = models.DecimalField(max_digits=10, decimal_places=2)
    no_transactions_fail = models.IntegerField()
    payment_reg_fail = models.IntegerField()
    paypal_payments = models.IntegerField()
    apple_payments = models.IntegerField()
    card_payments = models.IntegerField()
    bitcoin_payments = models.IntegerField()
    orders_fulfilled = models.IntegerField()
    orders_pending = models.IntegerField()
    orders_failed = models.IntegerField()
    trns_fail_order_fulfilled = models.IntegerField()
    duplicate_ip = models.IntegerField()
    duplicate_address = models.IntegerField()
    jcb_16 = models.IntegerField()
    american_exp = models.IntegerField()
    visa_16 = models.IntegerField()
    discover = models.IntegerField()
    voyager = models.IntegerField()
    visa_13 = models.IntegerField()
    maestro = models.IntegerField()
    mastercard = models.IntegerField()
    dc_cb = models.IntegerField()
    jcb_15 = models.IntegerField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()

    def __str__(self):
        return f"Ecommerce RePassed: {self.id}: {self.total_transaction_amt} total amount"  
    

class ECommerceErrorModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    no_transactions = models.IntegerField()
    no_orders = models.IntegerField()
    no_payments = models.IntegerField()
    total_transaction_amt = models.DecimalField(max_digits=10, decimal_places=2)
    no_transactions_fail = models.IntegerField()
    payment_reg_fail = models.IntegerField()
    paypal_payments = models.IntegerField()
    apple_payments = models.IntegerField()
    card_payments = models.IntegerField()
    bitcoin_payments = models.IntegerField()
    orders_fulfilled = models.IntegerField()
    orders_pending = models.IntegerField()
    orders_failed = models.IntegerField()
    trns_fail_order_fulfilled = models.IntegerField()
    duplicate_ip = models.IntegerField()
    duplicate_address = models.IntegerField()
    jcb_16 = models.IntegerField()
    american_exp = models.IntegerField()
    visa_16 = models.IntegerField()
    discover = models.IntegerField()
    voyager = models.IntegerField()
    visa_13 = models.IntegerField()
    maestro = models.IntegerField()
    mastercard = models.IntegerField()
    dc_cb = models.IntegerField()
    jcb_15 = models.IntegerField()
    phone = models.CharField(max_length=245)
    reason = models.CharField(max_length=255)
    verified = models.BooleanField()

    def __str__(self):
        return f"Ecommerce ErrorLog: {self.id}: {self.total_transaction_amt} total amount"  