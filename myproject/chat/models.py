# chat/models.py
from django.db import models
from authentication.models import Customer

class ChatMessage(models.Model):
    booking = models.ForeignKey('Bookings.Booking', on_delete=models.CASCADE)
    sender = models.ForeignKey(Customer, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(Customer, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
