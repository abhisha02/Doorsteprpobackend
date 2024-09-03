from django.contrib import admin
from . models import Customer,JobProfile,Otpstore

# Register your models here.
admin.site.register(Customer)
admin.site.register(JobProfile)
admin.site.register(Otpstore)
