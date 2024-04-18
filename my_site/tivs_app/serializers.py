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
    # email = serializers.EmailField()
    # password = serializers.CharField()

    # def validate(self, attrs):
    #     email = attrs.get('email')
    #     password = attrs.get('password')

    #     if email and password:
    #         user = authenticate(email=email, password=password)
    #         if not user:
    #             raise ValidationError('Invalid email or password.')
    #     else:
    #         raise ValidationError('Email and password are required.')

    #     return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Model
        fields = ['email','username']    
