from rest_framework import serializers
from Services.models import Category, Service
from .models import Cart, CartItem,BookingItem,Booking,Address
from authentication.models import Customer
from authentication.serializers import CustomerSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Service
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    service = ServiceSerializer()
    category = CategorySerializer()
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    current_category = CategorySerializer()
    class Meta:
        model = Cart
        fields = '__all__'
        
class BookingItemSerializer(serializers.ModelSerializer):
    service = ServiceSerializer()
    service_name = serializers.CharField(source='service.name')
    duration = serializers.FloatField(source='service.duration')
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, source='amount')
    service_category_name = serializers.CharField(source='service.category.name')
    service_category_picture = serializers.ImageField(source='service.category.picture')
    class Meta:
        model = BookingItem
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    customer=CustomerSerializer(read_only=True)
    professional=CustomerSerializer(read_only=True)
    class Meta:
        model = Booking
        fields = '__all__'
        depth = 1 

from rest_framework import serializers
from .models import Booking

class BookingReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['rating', 'review']

    def update(self, instance, validated_data):
        instance.rating = validated_data.get('rating', instance.rating)
        instance.review = validated_data.get('review', instance.review)
        instance.status = Booking.BookingStatus.REVIEW_DONE
        instance.save()
        return instance



