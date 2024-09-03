# serializers.py
from rest_framework import serializers
from authentication.models import Customer,JobProfile


class AdminUserSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()  # Add this field
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'profile_pic', 'is_active']
    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profile:
            return request.build_absolute_uri(obj.profile.url)
        return None
    
class UserUpdateSerializer(serializers.ModelSerializer):
    profile = serializers.ImageField(required=False)  # Make profile optional
    class Meta:
        model = Customer
        fields = ['first_name', 'phone_number', 'email', 'is_active', 'profile']
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.email = validated_data.get('email', instance.email)
        instance.is_active = validated_data.get('is_active', instance.is_active) 
        # Handle profile image
        if 'profile' in validated_data:
            instance.profile = validated_data['profile']
        instance.save()
        return instance
    
class JobProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobProfile
        fields = ['gender', 'address', 'profession', 'years_of_exp', 'adhar_no','is_approved','is_rejected']

class ProfessionalSerializer(serializers.ModelSerializer):
    job_profile = JobProfileSerializer(source='jobprofile', required=False)
    profile = serializers.ImageField(required=False)
    average_rating = serializers.SerializerMethodField()
    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 'email', 'password',
            'is_email_verified', 'is_professional', 'job_profile', 'profile','average_rating'
        ]
        extra_kwargs = {
            'first_name': {'error_messages': {'required': 'Please provide the first name.'}},
            'last_name': {'error_messages': {'required': 'Please provide the last name.'}},
            'phone_number': {'error_messages': {'required': 'Please provide the phone number.'}},
            'email': {'error_messages': {'required': 'Please provide the email address.'}},
            'password': {'write_only': True},
        }
    def get_average_rating(self, obj):
        return obj.average_rating() or 0

    def create(self, validated_data):
        job_profile_data = validated_data.pop('jobprofile', {})
        profile_data = validated_data.pop('profile', None)
        # Ensure is_email_verified and is_professional are set to True
        validated_data['is_email_verified'] = True
        validated_data['is_professional'] = True
        # Create the user instance
        user_instance = Customer.objects.create(**validated_data)
        user_instance.set_password(validated_data['password'])
        user_instance.save()
        # Create JobProfile instance if data is provided
        if job_profile_data:
            JobProfile.objects.create(user=user_instance, **job_profile_data)
        # Save profile picture if provided
        if profile_data:
            user_instance.profile = profile_data
            user_instance.save()
        return user_instance
        
class ProfessionalUpdateSerializer(serializers.ModelSerializer):
    job_profile = JobProfileSerializer(required=False)
    profile = serializers.ImageField(required=False)  # Add this field
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'is_email_verified', 'is_professional', 'profile', 'job_profile']
    def update(self, instance, validated_data):
        job_profile_data = validated_data.pop('job_profile', {})
        profile = validated_data.pop('profile', None)
        # Update user fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.email = validated_data.get('email', instance.email)
        instance.is_email_verified = validated_data.get('is_email_verified', instance.is_email_verified)
        instance.is_professional = validated_data.get('is_professional', instance.is_professional)
        if profile:
            instance.profile = profile
        instance.save()
        # Update or create job profile
        if job_profile_data:
            job_profile, created = JobProfile.objects.get_or_create(user=instance)
            for attr, value in job_profile_data.items():
                setattr(job_profile, attr, value)
            job_profile.save()
        return instance
