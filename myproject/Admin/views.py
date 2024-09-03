from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView
from authentication.models import Customer,JobProfile
from .serializers import AdminUserSerializer, UserUpdateSerializer,ProfessionalSerializer,ProfessionalUpdateSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import send_mail
from django.conf import settings
from Bookings.models import Booking,BookingItem
from Services.models import Service,Category
from Bookings.serializers import BookingSerializer
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth

class AdminUserListCreateView(ListCreateAPIView):
    queryset =Customer.objects.filter(is_superuser=False, is_professional=False)
    serializer_class = AdminUserSerializer
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    parser_classes = (MultiPartParser, FormParser)

class AdminUserRetrieveView(RetrieveAPIView):
    queryset = Customer.objects.all()
    serializer_class = AdminUserSerializer
    lookup_field = 'id'
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        # Add logging
        return super().get(request, *args, **kwargs)
    
class AdminUserUpdateView(UpdateAPIView):
    queryset = Customer.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'id'
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AdminUserDeleteView(APIView):
    def delete(self, request, id):
        try:
            user = Customer.objects.get(id=id)
            user.is_active = not user.is_active
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Customer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
class AdminProfessionalListCreateView(ListCreateAPIView):
    queryset = Customer.objects.filter(is_professional=True)
    serializer_class = ProfessionalSerializer
    filter_backends = [SearchFilter]
    parser_classes = (MultiPartParser, FormParser)
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']

class AdminProfessionalRetrieveView(RetrieveAPIView):
    queryset = Customer.objects.filter(is_professional=True)
    serializer_class = ProfessionalSerializer
    lookup_field = 'id'

class AdminProfessionalUpdateView(UpdateAPIView):
    queryset = Customer.objects.filter(is_professional=True)
    serializer_class = ProfessionalUpdateSerializer
    lookup_field = 'id'
    
class AdminProfessionalDeactivateActivateView(APIView):
    def patch(self, request, id):
        try:
            user = Customer.objects.get(id=id, is_professional=True)
            user.is_active = not user.is_active
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Customer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
class ApproveProfessionalView(APIView):
    def patch(self, request, id):
        try:
            customer= Customer.objects.get(id=id)
            professional=JobProfile.objects.get(user=customer)
            professional.is_approved = True
            professional.is_rejected = False
            professional.save()
            
            # Optionally, send an approval email or notification here
            send_mail(
                'Application Approved',
                'We are pleased to inform you that your application has been approved. Congratulations! We look forward to working with you and are excited about the opportunities ahead. If you have any questions or need further information, please feel free to reach out.',
                 settings.DEFAULT_FROM_EMAIL,
               [ customer.email],
                  fail_silently=False,
              )

            return Response({"message": "Professional approved successfully"}, status=status.HTTP_200_OK)
        except JobProfile.DoesNotExist:
            return Response({"error": "Professional not found"}, status=status.HTTP_404_NOT_FOUND)

class RejectProfessionalView(APIView):
    def patch(self, request, id):
        try:
            customer= Customer.objects.get(id=id)
            professional=JobProfile.objects.get(user=customer)
            professional.is_approved = False
            professional.is_rejected = True
            professional.save()
            
            # Send rejection email
            send_mail(
                'Application Rejected',
                'Thank you for your interest in DoorStepPro. After careful consideration, we regret to inform you that your application has been rejected.',
                settings.DEFAULT_FROM_EMAIL,
                [customer.email],
                fail_silently=False,
            )

            return Response({"message": "Professional rejected and email sent successfully"}, status=status.HTTP_200_OK)
        except JobProfile.DoesNotExist:
            return Response({"error": "Professional not found"}, status=status.HTTP_404_NOT_FOUND)

class AdminBookingsListCreateView(ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
class AdminDashboardDataView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Existing code
        total_revenue = Booking.objects.filter(status=Booking.BookingStatus.COMPLETED).aggregate(Sum('price'))['price__sum'] or 0
        total_professionals = Customer.objects.filter(is_professional=True).count()
        total_customers = Customer.objects.filter(is_professional=False).count()
        booking_count = Booking.objects.count()

        # Top Professionals
        professionals = Customer.objects.filter(is_professional=True)
        top_professionals = []
        for professional in professionals:
            avg_rating = professional.average_rating() or 0
            top_professionals.append((professional, avg_rating))
        top_professionals.sort(key=lambda x: x[1], reverse=True)
        top_professionals = top_professionals[:10]  # Get top 10

        # Top Categories
        top_categories = Category.objects.annotate(
            avg_rating=Avg('booking__rating')
        ).filter(
            avg_rating__isnull=False
        ).order_by('-avg_rating')[:10]

        # New statistics
        # Price per category
        price_per_category = Booking.objects.values('category__name').annotate(total_price=Sum('price'))

        # Price per month
        price_per_month = Booking.objects.annotate(month=TruncMonth('date')).values('month').annotate(total_price=Sum('price')).order_by('month')

        # Total bookings per category
        bookings_per_category = Booking.objects.values('category__name').annotate(total_bookings=Count('id'))

        data = {
            'total_revenue': total_revenue,
            'total_professionals': total_professionals,
            'total_customers': total_customers,
            'booking_count': booking_count,
            'top_professionals': [
                {'name': f"{pro[0].first_name} {pro[0].last_name}", 'rating': pro[1]}
                for pro in top_professionals
            ],
            'top_categories': [
                {'name': category.name, 'rating': round(category.avg_rating, 2) if category.avg_rating else None}
                for category in top_categories
            ],
            # New data
            'price_per_category': [
                {'category': item['category__name'], 'total_price': item['total_price']}
                for item in price_per_category
            ],
            'price_per_month': [
                {'month': item['month'].strftime('%Y-%m'), 'total_price': item['total_price']}
                for item in price_per_month
            ],
            'bookings_per_category': [
                {'category': item['category__name'], 'total_bookings': item['total_bookings']}
                for item in bookings_per_category
            ],
        }
        return Response(data)
    