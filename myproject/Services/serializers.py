from rest_framework import serializers
from .models import Category,Service

class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
   
    class Meta:
        model = Service
        fields = ['id', 'name', 'price', 'image', 'description', 'category', 'category_name', 'rating', 'is_listed', 'duration']
        extra_kwargs = {
            'image': {
                'required': False,        # Allow image to be optional
                'allow_null': True,       # Allow image to be null
                'allow_empty_file': True  # Allow empty image files
            }
        }

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    def create(self, validated_data):
        print('Validated Data:', validated_data)
        instance = super().create(validated_data)
        print('Instance Created:', instance)
        return instance

class CategorySerializer(serializers.ModelSerializer):
    latest_services = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'picture', 'description', 'is_listed', 'latest_services']
        extra_kwargs = {
            'picture': {
                'required': False,
                'allow_null': True,
                'allow_empty_file': True
            }
        }

    def create(self, validated_data):
        if 'is_listed' not in validated_data:
            validated_data['is_listed'] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr != 'is_listed':
                setattr(instance, attr, value)
        instance.save()
        return instance

    def get_latest_services(self, obj):
        services = obj.services.filter(is_listed=True).order_by('-date_created')[:4]
        context = self.context  # Pass the context to the ServiceSerializer
        return ServiceSerializer(services, many=True, context=context).data