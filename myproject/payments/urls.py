from django.urls import path
from .views import initiate_payment, payment_success,payment_failed

urlpatterns = [
    # ... other urls
    path('initiate_payment/', initiate_payment, name='initiate_payment'),
    path('payment_success/', payment_success, name='payment_success'),
    path('payment-failed/', payment_failed, name='payment_failed'),
]