from rest_framework import status,generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, CartItem, Service,Booking,BookingItem,Address,ProfessionalRating
from .serializers import CartSerializer, CartItemSerializer,BookingSerializer,BookingItemSerializer,AddressSerializer,BookingReviewSerializer,ServiceSerializer
from django.utils import timezone
from datetime import datetime
from authentication.models import JobProfile
from rest_framework.exceptions import NotFound
from django.db.models import Avg
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.apps import apps
from datetime import timedelta
from django.db.models import Avg
from .models import Booking
from authentication.models import Customer,JobProfile
from django.db.models import F, ExpressionWrapper, FloatField


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, service_id):
        user = request.user
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({"error": "Service not found"}, status=status.HTTP_404_NOT_FOUND)
        category = service.category
        try:
            cart = Cart.objects.get(customer=user)
        except Cart.DoesNotExist:
            cart = None
        if cart and cart.current_category != category:
            response = {"message": "Your cart contains items from another category. Do you want to replace them?"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        if not cart:
            cart = Cart.objects.create(customer=user, current_category=category)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            service=service,
            category=category,
            defaults={'quantity': 1, 'amount': service.price}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.amount = cart_item.quantity * service.price
            cart_item.save()
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)

class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(customer=user)
            cart.items.all().delete()
            cart.delete()
            return Response({"message": "Cart cleared successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
        
class CartView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            cart = Cart.objects.get(customer=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            serializer = CartItemSerializer(cart_items, many=True)
            return Response({"items": serializer.data}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"items": []}, status=status.HTTP_200_OK)

class CartItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, cart__customer=request.user)
            quantity = request.data.get('quantity', item.quantity)
            if quantity < 1 or quantity > 3:
                return Response({"error": "Quantity must be between 1 and 3"}, status=status.HTTP_400_BAD_REQUEST)
            item.quantity = quantity
            item.amount = item.quantity * item.service.price
            item.save()
            serializer = CartItemSerializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

class CartItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, cart__customer=request.user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

class CreateBookingView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response({"detail": "Cart ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(id=cart_id, customer=user)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)
        # Create a Booking instance
        booking = Booking.objects.create(
            customer=user,
            professional=None,  # Set to None initially
            date=datetime.now().date(),  # You might want to adjust this as needed
            time=datetime.now().time(),  # You might want to adjust this as needed
            price=0.0,  # Placeholder, will update after calculating total
            status=Booking.BookingStatus.PENDING,
            address=None  # Set to None initially
        )
        total_price = 0
        cart_items = CartItem.objects.filter(cart=cart)
        categories = set(item.category for item in cart_items)
        if categories:
            booking.category = categories.pop()
        for item in cart_items:
            BookingItem.objects.create(
                booking=booking,
                service=item.service,
                category=item.category,
                quantity=item.quantity,
                amount=item.amount
            )
            total_price += item.amount
        # Update booking price
        booking.price = total_price
        booking.save()
        # Optionally, clear the cart
        cart.items.all().delete()
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
    
class RetrieveBookingView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, booking_id, *args, **kwargs):
        try:
            booking = Booking.objects.get(id=booking_id, customer=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
class UpdateBookingItemQuantityView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, booking_item_id, *args, **kwargs):
        try:
            booking_item = BookingItem.objects.get(id=booking_item_id, booking__customer=request.user)
        except BookingItem.DoesNotExist:
            return Response({"detail": "Booking item not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get('quantity')
        if quantity is None:
            return Response({"detail": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(quantity, int) or quantity < 0:
            return Response({"detail": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)
        booking_item.quantity = quantity
        booking_item.amount = booking_item.service.price * quantity
        booking_item.save()

        # Optionally, update the booking total price
        booking = booking_item.booking
        booking.price = sum(item.amount for item in booking.items.all())
        booking.save()
        serializer = BookingItemSerializer(booking_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class RemoveBookingItemView(APIView):
    def delete(self, request, item_id):
        try:
            item = BookingItem.objects.get(id=item_id)
            item.delete()
            return Response({'message': 'Item removed successfully'}, status=status.HTTP_204_NO_CONTENT)
        except BookingItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

class AddressUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)

class AssignAddressToBookingView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()

    def update(self, request, *args, **kwargs):
        booking_id = kwargs.get('booking_id')
        address_id = request.data.get('address_id')
        address_pincode = request.data.get('address_pincode')

        try:
            booking = Booking.objects.get(id=booking_id, customer=request.user)
            address = Address.objects.get(id=address_id, customer=request.user)
            
            booking.address = address
            booking.address_pincode = address_pincode
            booking.save()

            return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)
        except (Booking.DoesNotExist, Address.DoesNotExist):
            return Response({"detail": "Booking or Address not found."}, status=status.HTTP_404_NOT_FOUND)
        
class AddressDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)
    
class SelectSlotView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        booking_id = request.data.get('booking_id')
        date = request.data.get('date')
        time = request.data.get('time')
        if not booking_id or not date or not time:
            return Response({"detail": "Booking ID, date, and time are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            booking = Booking.objects.get(id=booking_id, customer=user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)
        # Update the booking with the selected date and time
        booking.date = date
        booking.time = time
        booking.save()
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class UpdateBookingStatusView(APIView):
    def patch(self, request, booking_id):
        try:
            # Log debug information
            print(f"Received request to update booking {booking_id}")

            # Retrieve the booking object
            booking = Booking.objects.get(id=booking_id)
            print(f"Current status: {booking.status}")

            # Update the booking status to "Created"
            booking.status = Booking.BookingStatus.CREATED
            booking.save()
            print(f"Updated status to: {booking.status}")

            # Assign the temp_professional field only if the status is "Created" or "Professional_Not_Available"
            if booking.status in [Booking.BookingStatus.CREATED, Booking.BookingStatus.PROFESSIONAL_NOT_AVAILABLE]:
                self.assign_temp_professional(booking)

            # Notify the relevant professionals
            notify_professionals_of_new_booking(booking)

            return Response({'message': 'Booking status updated to Created successfully.'}, status=status.HTTP_200_OK)

        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def assign_temp_professional(self, booking):
        # Get the list of professionals sorted by their average rating in descending order
        professionals = Customer.objects.filter(
        is_professional=True,
        jobprofile__is_approved=True,
        jobprofile__profession=booking.category, 
        jobprofile__address_pincode=booking.address_pincode
            )
        print(professionals)
        rated_professionals = []
        for professional in professionals:
            avg_rating = professional.average_rating() or 0
            rated_professionals.append((professional, avg_rating))
    
    # Sort the list by average rating in descending order
        rated_professionals.sort(key=lambda x: x[1], reverse=True)
        print(rated_professionals)
        
        # Assign the first professional in the sorted list to the temp_professional field
        if rated_professionals:
            top_professional, _ = rated_professionals[0]
            booking.temp_professional = top_professional
            booking.temp_professional_updated_at = timezone.now()
            booking.save()
        else:
            # If there are no professionals available, set the status to "Professional_Not_Available"
            booking.status = Booking.BookingStatus.PROFESSIONAL_NOT_AVAILABLE
            booking.temp_professional = None
            booking.temp_professional_updated_at = None
            booking.save()

       

def notify_professionals_of_new_booking(booking):
    channel_layer = get_channel_layer()
    booking_data = {
        'id': booking.id,
        'date': booking.date.isoformat(),
        'time': booking.time.isoformat(),
        'status': booking.status,
        'is_new': True,
        'category': {
            'name': booking.category.name,
            'picture': f"http://127.0.0.1:8000{booking.category.picture.url}" if booking.category and booking.category.picture else None
        },
        'customer': {
            'first_name': booking.customer.first_name,
            'last_name': booking.customer.last_name
        },
        'address': {
            'address_line_1': booking.address.address_line_1,
            'city': booking.address.city,
            'state': booking.address.state,
            'country': booking.address.country,
            'zip_code': booking.address.zip_code
        },
        'items': [
            {
                'id': item.id,
                'service_name': item.service.name,
                'quantity': item.quantity,
                'duration': item.service.duration
            } for item in booking.items.all()
        ]
    }

    # Notify the temp_professional
    if booking.temp_professional:
        async_to_sync(channel_layer.group_send)(
            f'user_{booking.temp_professional.id}',
            {
                'type': 'booking_created',
                'booking': booking_data
            }
        )
        
class UserBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            Q(customer=user) &
            Q(status__in=[
                Booking.BookingStatus.CREATED,
                Booking.BookingStatus.TASK_DONE,
                Booking.BookingStatus.PROFESSIONAL_ASSIGNED,
                Booking.BookingStatus.PROFESSIONAL_NONE,
                Booking.BookingStatus.RESCHEDULED,
                 Booking.BookingStatus.PROFESSIONAL_NOT_AVAILABLE,

            ])
        ).order_by('-date_created')
    
class UpdateBookingStatusViewRescheduled(APIView):
    def patch(self, request, booking_id):
        try:
            # Log debug information
            print(f"Received request to update booking {booking_id}")
            # Retrieve the booking object
            booking = Booking.objects.get(id=booking_id)
            print(f"Current status: {booking.status}")
            # Update the booking status to "Rescheduled"
            booking.status = "rescheduled"
            booking.save()
            print(f"Updated status to: {booking.status}")
            return Response({'message': 'Booking status updated to Rescheduled successfully.'}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class BookingDeleteView(APIView):
    def delete(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            professional_id = booking.professional.id if booking.professional else None
            booking.delete()
            if professional_id:
                channel_layer = get_channel_layer()
                print("hi")
                async_to_sync(channel_layer.group_send)(
                    f'professional_{professional_id}',
                    {
                        'type': 'booking_cancelled',
                        'booking_id': booking_id
                    }
                )
            
            return Response({'message': 'Booking deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
       
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ProBookingsRequestsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            job_profile = JobProfile.objects.get(user=user)
            profession = job_profile.profession
            queryset = Booking.objects.filter(
                Q(temp_professional=user) &
                Q(status__in=[
                    Booking.BookingStatus.CREATED,
                    Booking.BookingStatus.RESCHEDULED,
                    Booking.BookingStatus.PROFESSIONAL_NOT_AVAILABLE,
                ])
            ).exclude(rejected_by=user).order_by('-date_created')
            return queryset
        except JobProfile.DoesNotExist:
            return Booking.objects.none()

class ProfessionalAcceptBookingView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
        # Update the booking status and assign the professional
        booking.status = Booking.BookingStatus.PROFESSIONAL_ASSIGNED
        booking.professional = request.user  # Assuming the logged-in user is a Customer
        booking.save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{booking.customer.id}',
            {
                'type': 'booking_updated',
                'booking': {
                    'id': booking.id,
                    'status': booking.status,
                    'professional': {
                        'id': booking.professional.id,
                        'name': f"{booking.professional.first_name} {booking.professional.last_name}"
                    }
                }
            }
        )

        return Response({'message': 'Booking status updated to Professional_assigned successfully.'}, status=status.HTTP_200_OK)
       
class ProfessionalRejectBookingView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id):
        user = request.user
        try:
            booking = Booking.objects.get(id=booking_id)
            
            # Check if the user is authorized to reject this booking
            if booking.temp_professional != user:
                raise NotFound(detail='You are not authorized to reject this booking.')
            
            booking.rejected_by.add(user)
            booking.professional = None
            booking.pro_flag = True
            booking.save()

            professionals = Customer.objects.filter(
                is_professional=True,
                jobprofile__is_approved=True,
                jobprofile__profession=booking.category, 
                jobprofile__address_pincode=booking.address_pincode
                    )
            
            rated_professionals = []
            for professional in professionals:
                avg_rating = professional.average_rating() or 0
                rated_professionals.append((professional, avg_rating))
    
    # Sort the list by average rating in descending order
            rated_professionals.sort(key=lambda x: x[1], reverse=True)
            next_professional = self.get_next_professional(rated_professionals, booking.temp_professional)
            if next_professional:
                booking.temp_professional = next_professional
                booking.save()
            else:
                booking.status = Booking.BookingStatus.PROFESSIONAL_NOT_AVAILABLE
                booking.temp_professional = None
                booking.save()

            # Notify professionals of the rejection and update
            self.notify_booking_rejected(booking)

            return Response({'message': 'Booking rejected successfully.'}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            raise NotFound(detail='Booking not found.')

    def get_next_professional(self, rated_professionals, current_professional):
        for i, (professional, _) in enumerate(rated_professionals):
            if professional == current_professional:
                if i + 1 < len(rated_professionals):
                    return rated_professionals[i + 1][0]  # Return the next professional
                else:
                    return None  # No more professionals after the current one
        return rated_professionals[0][0] if rated_professionals else None  # Return the first professional if current not found

    def notify_booking_rejected(self, booking):
        channel_layer = get_channel_layer()
        booking_data = self.get_booking_data(booking)

        # Notify all professionals
        async_to_sync(channel_layer.group_send)(
            'professionals',
            {
                'type': 'booking_rejected',
                'booking': booking_data
            }
        )

        # Notify the new temp_professional if exists
        if booking.temp_professional:
            async_to_sync(channel_layer.group_send)(
                f'user_{booking.temp_professional.id}',
                {
                    'type': 'booking_created',
                    'booking': booking_data
                }
            )

    def get_booking_data(self, booking):
        return {
            'id': booking.id,
            'date': booking.date.isoformat(),
            'time': booking.time.isoformat(),
            'status': booking.status,
            'is_new': False,
            'category': {
                'name': booking.category.name,
                'picture': f"http://127.0.0.1:8000{booking.category.picture.url}" if booking.category and booking.category.picture else None
            },
            'customer': {
                'first_name': booking.customer.first_name,
                'last_name': booking.customer.last_name
            },
            'address': {
                'address_line_1': booking.address.address_line_1,
                'city': booking.address.city,
                'state': booking.address.state,
                'country': booking.address.country,
                'zip_code': booking.address.zip_code
            },
            'items': [
                {
                    'id': item.id,
                    'service_name': item.service.name,
                    'quantity': item.quantity,
                    'duration': item.service.duration
                } for item in booking.items.all()
            ],
            'temp_professional': booking.temp_professional.id if booking.temp_professional else None,
            
        }
class ProfessionalActiveTasksView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            Q(professional=user) &
            Q(status__in=[
                Booking.BookingStatus.PROFESSIONAL_ASSIGNED,
                Booking.BookingStatus.RESCHEDULED,
                Booking.BookingStatus.TASK_DONE,
                Booking.BookingStatus.PAYMENT_DONE,
            ])
        ).order_by('-date_created')
class ProfessionalCancelBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        booking_id = request.data.get('booking_id')

        if not booking_id:
            return Response({'error': 'Booking ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.get(id=booking_id)

            # Ensure the current user is the professional who can cancel the booking
            if request.user != booking.professional:
                return Response({'error': 'You are not authorized to reject this booking.'}, status=status.HTTP_403_FORBIDDEN)
            # Update booking status and fields
            booking.status = Booking.BookingStatus.PROFESSIONAL_NONE
            booking.professional = None
            booking.rejected_by.add(request.user)  # Add the rejecting professional
            booking.save()
            professionals = Customer.objects.filter(
                is_professional=True,
                jobprofile__is_approved=True,
                jobprofile__profession=booking.category, 
                jobprofile__address_pincode=booking.address_pincode
                    )
            
            rated_professionals = []
            for professional in professionals:
                avg_rating = professional.average_rating() or 0
                rated_professionals.append((professional, avg_rating))
    
    # Sort the list by average rating in descending order
            rated_professionals.sort(key=lambda x: x[1], reverse=True)
            next_professional = self.get_next_professional(rated_professionals, booking.temp_professional)
            if next_professional:
                booking.temp_professional = next_professional
                booking.save()
            else:
                booking.status = Booking.BookingStatus.PROFESSIONAL_NOT_AVAILABLE
                booking.temp_professional = None
                booking.save()

            # Notify professionals of the rejection and update
            self.notify_booking_rejected(booking)

            return Response({'message': 'Booking rejected successfully.'}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            raise NotFound(detail='Booking not found.')

    def get_next_professional(self, rated_professionals, current_professional):
        for i, (professional, _) in enumerate(rated_professionals):
            if professional == current_professional:
                if i + 1 < len(rated_professionals):
                    return rated_professionals[i + 1][0]  # Return the next professional
                else:
                    return None  # No more professionals after the current one
        return rated_professionals[0][0] if rated_professionals else None  # Return the first professional if current not found

    def notify_booking_rejected(self, booking):
        channel_layer = get_channel_layer()
        booking_data = self.get_booking_data(booking)

        # Notify all professionals
        async_to_sync(channel_layer.group_send)(
            'professionals',
            {
                'type': 'booking_rejected',
                'booking': booking_data
            }
        )

        # Notify the new temp_professional if exists
        if booking.temp_professional:
            async_to_sync(channel_layer.group_send)(
                f'user_{booking.temp_professional.id}',
                {
                    'type': 'booking_created',
                    'booking': booking_data
                }
            )

    def get_booking_data(self, booking):
        return {
            'id': booking.id,
            'date': booking.date.isoformat(),
            'time': booking.time.isoformat(),
            'status': booking.status,
            'is_new': False,
            'category': {
                'name': booking.category.name,
                'picture': f"http://127.0.0.1:8000{booking.category.picture.url}" if booking.category and booking.category.picture else None
            },
            'customer': {
                'first_name': booking.customer.first_name,
                'last_name': booking.customer.last_name
            },
            'address': {
                'address_line_1': booking.address.address_line_1,
                'city': booking.address.city,
                'state': booking.address.state,
                'country': booking.address.country,
                'zip_code': booking.address.zip_code
            },
            'items': [
                {
                    'id': item.id,
                    'service_name': item.service.name,
                    'quantity': item.quantity,
                    'duration': item.service.duration
                } for item in booking.items.all()
            ],
            'temp_professional': booking.temp_professional.id if booking.temp_professional else None,
            
        }
        
class ProfessionalConfirmRescheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        if not booking_id:
            return Response({"error": "Booking ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = Booking.BookingStatus.PROFESSIONAL_ASSIGNED
            booking.save()
            return Response({"success": "Booking status updated to Professional Assigned"}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
class TaskDoneView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking = Booking.objects.get(id=booking_id)

        if booking.status != Booking.BookingStatus.PROFESSIONAL_ASSIGNED:
            return Response({"detail": "Invalid booking status."}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = Booking.BookingStatus.TASK_DONE
        booking.save()

        # Create ProfessionalRating object
        ProfessionalRating.objects.create(
            professional=booking.professional,
            booking=booking,
            score=None  # Assuming a default score of 5 for demonstration
        )

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
class  PaymentReceivedView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking = Booking.objects.get(id=booking_id)

        if booking.status != Booking.BookingStatus.TASK_DONE:
            return Response({"detail": "Invalid booking status."}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = Booking.BookingStatus.PAYMENT_DONE
        booking.save()
        return Response({'message': 'Status updated  successfully.'}, status=status.HTTP_200_OK)
class   CloseBookingView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking = Booking.objects.get(id=booking_id)

        if booking.status != Booking.BookingStatus.PAYMENT_DONE:
            return Response({"detail": "Invalid booking status."}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = Booking.BookingStatus. COMPLETED
        booking.save()
        return Response({'message': 'Status updated  successfully.'}, status=status.HTTP_200_OK)

        
class UserBookingsReviewPageView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            Q(customer=user) &
            Q(status=Booking.BookingStatus.COMPLETED)
        ).order_by('-date_created')[:7]

class BookingReviewView(APIView):
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BookingReviewSerializer(booking, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class UserBookingsHistoryPageView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            Q(customer=user) &
            Q(status__in=[Booking.BookingStatus.REVIEW_DONE, Booking.BookingStatus.COMPLETED])
        ).order_by('-date_created')[:7] 
    
class ProfessionalTasksHistoryView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            Q(professional=user) &
            Q(status__in=[
                Booking.BookingStatus.COMPLETED,
                Booking.BookingStatus.REVIEW_DONE,
            ])
        ).order_by('-date_created')
class FavouriteServicesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Fetch the latest 5 bookings for the user
        bookings = Booking.objects.filter(customer=user).order_by('-date_created')[:5]
        
        # Collect all service IDs from the BookingItems of these bookings
        service_ids = set()
        for booking in bookings:
            booking_items = BookingItem.objects.filter(booking=booking)
            service_ids.update(booking_items.values_list('service_id', flat=True))
        
        # Fetch all services with those IDs
        services = Service.objects.filter(id__in=service_ids)
        
        # Serialize the services
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)
class ProfessionalAchievementView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            professional=user,
            status__in=[Booking.BookingStatus.COMPLETED, Booking.BookingStatus.REVIEW_DONE]
        ) 
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        bookings = serializer.data
        # Calculate average rating
        avg_rating = Booking.objects.filter(
            professional=request.user,
            status__in=[Booking.BookingStatus.COMPLETED, Booking.BookingStatus.REVIEW_DONE]
        ).aggregate(Avg('rating'))['rating__avg'] or 0
        
        return Response({
            'bookings': bookings,
            'average_rating': avg_rating
        })