from django.urls import include, path
from . import views
from rest_framework_simplejwt import views as jwt_views
from .views import OTPVerificationView,SendEmailUpdateOTPView,VerifyEmailUpdateOTPView,PasswordResetRequestView,OtpVerificationResetpasswordView,PasswordResetView,GoogleLogin
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns =[
 path("", views.getAccountsRoutes.as_view(), name="accounts-routes"),
 path("register2/", views.RegistrationView.as_view(), name="user-register"),
 path('otp-verification/',OTPVerificationView.as_view(), name='otp_verification'),
 path("login/", views.LoginView.as_view(), name="user-login"),
 path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
 path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
 path("user/details/", views.UserDetails.as_view(), name="user-details"), 
 path("user/details/edit",views.UserDetailsEdit.as_view(),name="user-details-edit"),
 path("current/", views.UserView.as_view(), name="user-current"),
 path('send-email-update-otp/', SendEmailUpdateOTPView.as_view(), name='send-email-update-otp'),
 path('verify-email-update-otp/', VerifyEmailUpdateOTPView.as_view(), name='verify-email-update-otp'),
 path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
 path('reset-password/verify-otp/', OtpVerificationResetpasswordView.as_view(), name='verify_otp'),
 path('reset-password/', PasswordResetView.as_view(), name='reset_password'),


#Professionals
path("professional/details/", views.ProfessionalDetails.as_view(), name="profesional-details"), 
path("professional/details/update", views.ProfessionalDetailsUpdate.as_view(), name="professional-details-update"),
path("professional/details/edit",views.ProUserDetailsEdit.as_view(),name="professional-details-edit"),
path('auth/google/', GoogleLogin.as_view(), name='google_login'),







    
]