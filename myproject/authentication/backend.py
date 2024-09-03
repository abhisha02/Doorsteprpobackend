from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Professional

class ProfessionalBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            professional = Professional.objects.get(email=email)
            if professional.check_password(password):
                return professional
        except Professional.DoesNotExist:
            return None
