from django.contrib import admin
from .models import Cart,CartItem,Booking,BookingItem

# Register your models here.
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Booking)
admin.site.register(BookingItem)