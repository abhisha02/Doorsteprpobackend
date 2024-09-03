import razorpay
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from Bookings.models import Booking
from Bookings.serializers import BookingSerializer

@api_view(['POST'])
def initiate_payment(request):
    booking_id = request.data.get('booking_id')
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)

    amount = int(booking.price * 100)  # Convert to paise
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })
    
    booking.razorpay_order_id = payment['id']
    booking.save()
    
    data = {
        "payment": payment,
        "booking": BookingSerializer(booking).data
    }
    return Response(data)

@api_view(['POST'])
def payment_success(request):
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_signature = request.data.get('razorpay_signature')
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        booking = Booking.objects.get(razorpay_order_id=razorpay_order_id)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)
    
    data = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    
    check = client.utility.verify_payment_signature(data)
    
    if check:
        booking.status = Booking.BookingStatus.PAYMENT_DONE
        booking.save()
        return Response({'status': 'Payment successful'})
    else:
        return Response({'status': 'Payment failed'}, status=400)
@api_view(['POST'])
def payment_failed(request):
    razorpay_order_id = request.data.get('razorpay_order_id')
    
    try:
        booking = Booking.objects.get(razorpay_order_id=razorpay_order_id)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)
    
    # Assuming you have a PAYMENT_FAILED status in your Booking model
    booking.status = Booking.BookingStatus.PAYMENT_FAILED
    booking.save()
    
    # You can add any additional logic here, such as sending notifications
    
    return Response({
        'status': 'Payment failed',
        'booking_id': booking.id,
        'message': 'The payment for this booking has failed. Please try again or contact support.'
    })