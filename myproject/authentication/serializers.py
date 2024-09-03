from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from rest_framework import serializers
from .models import Customer,Otpstore,JobProfile
from rest_framework_simplejwt.tokens import RefreshToken, Token,AccessToken
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from Services.models import Category



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['first_name'] = Customer.first_name
        # ...
        
        return token
    
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id','email', 'phone_number', 'first_name', 'last_name', 'password','profile']  # Include 'password' if you want to accept it during registration
        extra_kwargs = {
            'password': {'write_only': True},  # Ensures password is write-only
        }
    def create(self, validated_data):
        user = Customer.objects.create_user(**validated_data)
        return user
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class JobProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobProfile
        fields = ['gender', 'address', 'profession', 'years_of_exp', 'adhar_no','address_pincode']

class ProfessionalRegistrationSerializer(serializers.ModelSerializer):
    job_profile = JobProfileSerializer()
    class Meta:
        model = Customer
        fields = ['email', 'phone_number', 'first_name', 'password', 'job_profile']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensures password is write-only
        }
    def create(self, validated_data):
        job_profile_data = validated_data.pop('job_profile')
        user = Customer.objects.create_user(**validated_data)
        JobProfile.objects.create(user=user, **job_profile_data)
        user.is_professional = True
        user.save()
        return user
    

    
class UserSerializer(serializers.ModelSerializer):
    profile = serializers.ImageField(max_length=None, use_url=True)
    class Meta:
        model = Customer
        exclude = ('password',)






class ProfessionalSerializer(serializers.ModelSerializer):
    job_profile = JobProfileSerializer(source='jobprofile')
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'is_email_verified', 'profile', 'job_profile']
   

        
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OtpVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField()

class PasswordResetSerializer(serializers.Serializer):
    otp = serializers.CharField()
    new_password = serializers.CharField()
