from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import render
from .serializers import CustomerSerializer,UserSerializer,ProfessionalRegistrationSerializer,ProfessionalSerializer,JobProfileSerializer,PasswordResetRequestSerializer,OtpVerificationSerializer,PasswordResetSerializer
from .models import Customer,Otpstore,JobProfile
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ParseError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework import serializers
from cryptography.fernet import Fernet
import hashlib
from Services.models import Category
from django.db.models import Avg
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class getAccountsRoutes(APIView):
     def get(self, request, format=None):
        routes = [
        'login',
        'register',
                    ]
        return Response(routes)        
class RegistrationView(APIView):
    authentication_classes = []
    def post(self, request):
        if Customer.objects.filter(phone_number=request.data['phone_number']).exists():
            return Response({'error': 'Phone number already exists', 'status': 'error_phone_number'}, status=status.HTTP_400_BAD_REQUEST)
        if Customer.objects.filter(email=request.data['email']).exists():
            return Response({'error': 'Email already exists', 'status': 'error_email'}, status=status.HTTP_400_BAD_REQUEST)
        if 'job_profile' in request.data:
            serializer = ProfessionalRegistrationSerializer(data=request.data)
        else:
            serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        otp = get_random_string(length=4, allowed_chars='1234567890')
        expiry = datetime.now() + timedelta(minutes=5)  # OTP expires in 5 minutes
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
        Otpstore.objects.create(user=user, hashed_otp=hashed_otp)
        
        subject = 'OTP verification'
        message = f'Hello {user.first_name},\n\n' \
                  f'Please use the following OTP to verify your email: {otp}\n\n' \
                  f'Thank you!'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        
        send_mail(subject, message, from_email, recipient_list)
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)

    
class OTPVerificationView(APIView):
    def post(self, request):
        # Extract OTP entered by the user
        entered_otp = request.data.get('otp')
        entered_otp = int(entered_otp)
        first_name = request.data.get('user')
        # Retrieve the stored OTP from the session
        user = Customer.objects.get(first_name=first_name)
        otp_instance = Otpstore.objects.get(user=user)
        # Hash entered OTP for comparison
        hashed_entered_otp = hashlib.sha256(str(entered_otp).encode()).hexdigest()
        # Compare hashed OTPs
        if hashed_entered_otp == otp_instance.hashed_otp:
       
            # OTP is valid, proceed with user registration 
            user.is_active = True
            user.is_email_verified=True
            # Save the user
            user.save()
            # delete otp from db
            otp_instance .delete()
            return Response({'message': 'Registration successful'}, status=status.HTTP_200_OK)
        else:
            # OTP is invalid
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            user = None
            return Response({
                'detail': 'User does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        if user is not None and user.check_password(password):
            refresh = RefreshToken.for_user(user)  # Generate refresh token
            is_professional = user.is_professional
            is_approved = False
            is_rejected=False
            if is_professional:
                try:
                    job_profile = JobProfile.objects.get(user=user)
                    is_approved = job_profile.is_approved
                    is_rejected=job_profile.is_rejected
                except JobProfile.DoesNotExist:
                    pass  # Job profile might not exist for some users
            if not user.is_active:
             return Response({
                'detail': 'You have been temporarily blocked by admin'
                }, status=status.HTTP_403_FORBIDDEN)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'isAdmin':user.is_superuser,
                'isProfessional':user.is_professional,
                'isApproved': is_approved ,
                'isRejected':is_rejected

               
                
            })
        else:
            return Response({
                'detail': 'Invalid credentials'
            }, status=status.HTTP_400_BAD_REQUEST)
          
class UserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        userEmail = Customer.objects.get(id=request.user.id).email
        content = {
            'user-email':userEmail,
            'user': str(request.user),  
            'auth': str(request.auth),  
        }
        return Response(content)
class UserDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = Customer.objects.get(id=request.user.id)
        data = UserSerializer(user).data  
        content = data
        return Response(content)
           
class ProfessionalDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = Customer.objects.get(id=request.user.id)
        # Serialize the user data
        serializer = ProfessionalSerializer(user)
        data = serializer.data

        # Calculate average rating
        average_rating = user.average_rating() or 0

        # Add average rating to the serialized data
        data['average_rating'] = average_rating

        return Response(data)
    
class ProfessionalDetailsUpdate(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        job_profile, created = JobProfile.objects.get_or_create(user=request.user)
        job_profile_serializer = JobProfileSerializer(job_profile, data=request.data, partial=True)
      
        if job_profile_serializer.is_valid():
            job_profile_serializer.save()
            response_data = job_profile_serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            errors = {}
            if not job_profile_serializer.is_valid():
                errors.update(job_profile_serializer.errors)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
class UserDetailsEdit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        # Update Customer fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.phone_number = request.data.get('phone_number', user.phone_number)
        # Handle profile picture upload
        profile_picture = request.FILES.get('profile_pic')
        if profile_picture:
            user.profile = profile_picture
        user.save()        
        return Response({'message': 'Details updated successfully'}, status=status.HTTP_200_OK)
class ProUserDetailsEdit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        # Update Customer fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.phone_number = request.data.get('phone_number', user.phone_number)
        # Handle profile picture upload
        profile_picture = request.FILES.get('profile_pic')
        if profile_picture:
            user.profile = profile_picture
        user.save()
        # Update JobProfile fields if the user has one
        if hasattr(user, 'jobprofile'):
            job_profile = user.jobprofile
            job_profile.gender = request.data.get('gender', job_profile.gender)
            job_profile.address = request.data.get('address', job_profile.address)
            job_profile.profession_id = request.data.get('profession', job_profile.profession_id)
            job_profile.years_of_exp = request.data.get('years_of_exp', job_profile.years_of_exp)
            job_profile.adhar_no = request.data.get('adhar_no', job_profile.adhar_no)
            job_profile.save()
        return Response({'message': 'Details updated successfully'}, status=status.HTTP_200_OK)
class SendEmailUpdateOTPView(APIView):
    def post(self, request):
        new_email = request.data.get('email')
        user = request.user  # Assuming the user is authenticated
        print(new_email)

        if Customer.objects.filter(email=new_email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        otp = get_random_string(length=4, allowed_chars='1234567890')
        expiry = datetime.now() + timedelta(minutes=5)  # OTP expires in 5 minutes
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
        Otpstore.objects.create(user=user, hashed_otp=hashed_otp)

        subject = 'OTP verification for email update'
        message = f'Hello {user.first_name},\n\n' \
                  f'Please use the following OTP to verify your new email: {otp}\n\n' \
                  f'Thank you!'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [new_email]

        send_mail(subject, message, from_email, recipient_list)
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
class VerifyEmailUpdateOTPView(APIView):
    def post(self, request):
        entered_otp = request.data.get('otp')
        entered_otp = int(entered_otp)
        new_email = request.data.get('email')
        user = request.user  # Assuming the user is authenticated

        otp_instance = Otpstore.objects.filter(user=user).first()
        if not otp_instance:
            return Response({'error': 'Invalid OTP or email'}, status=status.HTTP_400_BAD_REQUEST)

        hashed_entered_otp = hashlib.sha256(str(entered_otp).encode()).hexdigest()
        if hashed_entered_otp == otp_instance.hashed_otp:
            user.email = new_email
            user.is_email_verified = True
            user.save()
            otp_instance.delete()
            return Response({'message': 'Email updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        if not Customer.objects.filter(email=email).exists():
            return Response({'error': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)

        user = Customer.objects.get(email=email)
        otp = get_random_string(length=6, allowed_chars='1234567890')
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
        
        otp_instance, created = Otpstore.objects.get_or_create(user=user)
        otp_instance.set_otp(otp)

        subject = 'Password Reset OTP'
        message = f'Hello {user.first_name},\n\n' \
                  f'Please use the following OTP to reset your password: {otp}\n\n' \
                  f'Thank you!'
        from_email = 'your_email@example.com'
        recipient_list = [email]
        
        send_mail(subject, message, from_email, recipient_list)
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)

class OtpVerificationResetpasswordView(APIView):
    def post(self, request):
        serializer = OtpVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
        
        try:
            otp_instance = Otpstore.objects.get(hashed_otp=hashed_otp)
        except Otpstore.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
        
        try:
            otp_instance = Otpstore.objects.get(hashed_otp=hashed_otp)
        except Otpstore.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = otp_instance.user
        user.set_password(new_password)
        user.save()
        otp_instance.delete()

        response_data = {
            'message': 'Password has been reset successfully',
            'is_professional': user.is_professional
         }

        return Response(response_data, status=status.HTTP_200_OK)





class GoogleLogin(APIView):
    def post(self, request):
        credential = request.data.get('credential')
        
        logger.info(f"Received request for Google login. Credential present: {bool(credential)}")
        
        if not credential:
            logger.warning("Credential is missing in the request")
            return Response({'error': 'Credential is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Specify the CLIENT_ID of your app
            CLIENT_ID = "988251266326-j5n9pjaoesumpoo5262g3bhva18ij3hr.apps.googleusercontent.com"
            
            logger.info("Attempting to verify Google credential")
            # Verify the token
            id_info = id_token.verify_oauth2_token(credential, requests.Request(), CLIENT_ID)
            
            # Get user info from the decoded token
            user_email = id_info['email']
            given_name = id_info.get('given_name', '')
            family_name = id_info.get('family_name', '')
            
            logger.info(f"Successfully verified credential for email: {user_email}")
            
            # Check if user exists
            user, created = Customer.objects.get_or_create(
                email=user_email,
                defaults={
                    'first_name': given_name,
                    'last_name': family_name,
                    'is_email_verified': True,
                }
            )
            
            if created:
                logger.info(f"New user created with email: {user.email}")
                random_password = Customer.objects.make_random_password()
                user.set_password(random_password)
                user.save()
            else:
                logger.info(f"Existing user found with email: {user.email}")
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"User {user.email} is not active")
                return Response({
                    'detail': 'You have been temporarily blocked by admin'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check professional status
            is_professional = user.is_professional
            is_approved = False
            is_rejected = False
            if is_professional:
                try:
                    job_profile = JobProfile.objects.get(user=user)
                    is_approved = job_profile.is_approved
                    is_rejected = job_profile.is_rejected
                    logger.info(f"Professional status for {user.email}: approved={is_approved}, rejected={is_rejected}")
                except JobProfile.DoesNotExist:
                    logger.warning(f"No JobProfile found for professional user {user.email}")
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'isAdmin': user.is_superuser,
                'isProfessional': is_professional,
                'isApproved': is_approved,
                'isRejected': is_rejected
            }
            logger.info(f"Successful login for user {user.email}")
            return Response(response_data)
        
        except ValueError:
            logger.error("Invalid Google credential")
            return Response({'error': 'Invalid credential'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Unexpected error in Google login: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)