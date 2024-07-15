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

class CustomerData(models.Model):
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

    def __str__(self):
        return f"Customer Data: {self.id}"

class ErrorLogsModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    data = models.JSONField()
    error = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True) 