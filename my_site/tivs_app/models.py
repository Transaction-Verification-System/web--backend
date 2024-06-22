from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,BaseUserManager


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




