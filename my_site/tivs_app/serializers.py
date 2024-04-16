from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model,authenticate
from django.forms import ValidationError

User_Model = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Model
        fields='__all__'

        def create(self,clean_data):
            user_obj = User_Model.objects.create_user(email=clean_data['email'],username=clean_data['username'],password=clean_data['password'])
            user_obj.username = clean_data['username']

            user_obj.save()

            return user_obj

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


    def check(self,clean_data):
        user = authenticate(email = clean_data['email'],password = clean_data['password'])
        if not user:
            return ValidationError('Login Failed')
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Model
        fields = ['email','username']    
