from django.db import models
from authentication.models import Customer
from Services.models import Category,Service
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Create your models here.
class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    current_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"Cart {self.id} for customer {self.customer.id}"

class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"Item {self.id} in cart {self.cart.id}"
    


class Booking(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CREATED = 'created', _('Created')
        PROFESSIONAL_ASSIGNED = 'professional_assigned', _('Professional Assigned')
        PROFESSIONAL_NONE = 'professional_none', _('Professional None')  # New status added
        RESCHEDULED = 'rescheduled', _('Rescheduled')
        TASK_DONE = 'task_done', _('Task Done')
        PAYMENT_DONE = 'payment_done', _('Payment Done')
        PAYMENT_FAILED = 'payment_failed', _('Payment Failed')
        COMPLETED = 'completed', _('Completed')
        REVIEW_DONE = 'review_done', _('Review Done') 
        PROFESSIONAL_NOT_AVAILABLE='professional_not_available',_('Professional not Available')


    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    professional = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bookings')
    temp_professional = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True,related_name='assigned_bookings_temp')
    pro_flag=models.BooleanField(null=True, blank=True,default=False)
    date = models.DateField()
    time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=200,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    rejected_by = models.ManyToManyField(Customer, related_name='rejected_bookings', blank=True)
    rating = models.PositiveIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    review = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True,null=True,blank=True) 
    address_pincode = models.CharField(max_length=6, null=True, blank=True) 
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Booking {self.id} for {self.customer.first_name} {self.customer.last_name}"

class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"Item {self.id} in booking {self.booking.id}"
    
class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    date_created = models.DateTimeField(default=timezone.now) 
    def __str__(self):
        return f"{self.address_line_1}, {self.city}, {self.state}, {self.country} - {self.zip_code}"

class ProfessionalRating(models.Model):
    professional = models.ForeignKey(Customer, on_delete=models.CASCADE, limit_choices_to={'is_professional': True})
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)   # Rating from 1 to 5

    def __str__(self):
        return f"Rating {self.score} for Professional {self.professional.first_name} {self.professional.last_name} (Booking {self.booking.id})"

