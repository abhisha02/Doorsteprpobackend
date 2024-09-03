from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager,Group, Permission
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
import base64
from django.conf import settings
from hashlib import sha256
from Services.models import Category
from django.utils import timezone
from django.apps import apps
import re
import string
import random




class CustomerManager(BaseUserManager):
    def create_user(self, email, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
       

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, phone_number, password, **extra_fields)
    def make_random_password(self, length=10, allowed_chars=string.ascii_letters + string.digits + string.punctuation):
        """
        Generate a random password with the given length and allowed characters.
        """
        return ''.join(random.choice(allowed_chars) for i in range(length))

class Customer(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=12, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    is_email_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff=models.BooleanField(default=False)
    is_professional=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    profile= models.ImageField(upload_to='user/profile_pic/',null=True,blank=True)
    date_created = models.DateTimeField(default=timezone.now) 
    username=None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'first_name', 'last_name']
    objects = CustomerManager()
    def average_rating(self):
        # Use Django's apps.get_model to dynamically get the ProfessionalRating model
        Booking = apps.get_model('Bookings', 'Booking')
        ratings = Booking.objects.filter(professional=self)
        if ratings.exists():
            average = ratings.aggregate(models.Avg('rating'))['rating__avg']
            return round(average, 2) if average is not None else None
        return None
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Otpstore(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hashed_otp = models.CharField(max_length=64,null=True)  # Store hashed OTP here

    def set_otp(self, otp):
        # Hash OTP using hashlib.sha256 and store the hashed value
        self.hashed_otp = sha256(otp.encode()).hexdigest()
        self.save()

    def verify_otp(self, entered_otp):
        # Hash entered OTP and compare with stored hashed OTP
        hashed_entered_otp = sha256(entered_otp.encode()).hexdigest()
        return hashed_entered_otp == self.hashed_otp

    def __str__(self):
        return f"OTP for {self.user.email}"

class JobProfile(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)
    gender=models.CharField(max_length=20)
    address=models.TextField(max_length=300)
    profession = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    years_of_exp=models.FloatField()
    adhar_no=models.CharField(max_length=50)
    earned_points=models.IntegerField( blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False,null =True,blank=True)
    address_pincode = models.CharField(max_length=6, null=True, blank=True) 
   

    
