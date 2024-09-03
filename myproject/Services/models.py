from django.db import models
from django.utils import timezone
from django.conf import settings



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    picture = models.ImageField(upload_to='category_pictures/', null=True, blank=True)
    description = models.TextField(blank=True)
    is_listed = models.BooleanField(default=True)  # Added field for listed/unlisted state
    date_created = models.DateTimeField(default=timezone.now) 
    def __str__(self):
        return self.name
    def get_picture_url(self):
        if self.picture:
            return f"{settings.MEDIA_URL}{self.picture}"
        return None
    
class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='service_images/', null=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services')
    rating = models.FloatField(default=0.0) 
    duration = models.FloatField(default=0.0) 
    is_listed = models.BooleanField(default=True) # Default rating is 0.0
    date_created = models.DateTimeField(default=timezone.now) 
    def __str__(self):
        return self.name

