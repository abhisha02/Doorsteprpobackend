from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from .models import Category,Service
from .serializers import CategorySerializer,ServiceSerializer
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

class AdminCategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('-date_created') 
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']
    def perform_create(self, serializer):
        # Ensure 'is_listed' is True when creating a new category
        serializer.save(is_listed=True)

class AdminCategoryRetrieveView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'

class AdminCategoryUpdateView(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            print(serializer.errors)  # Log serializer errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminCategoryDeleteView(generics.DestroyAPIView):  # Use DestroyAPIView for delete
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'

class ToggleCategoryListing(APIView):
    def post(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        # Toggle the is_listed field
        category.is_listed = not category.is_listed
        category.save()
        return Response({'message': 'Category listing status toggled successfully.'}, status=status.HTTP_200_OK)
    
class AdminServiceListCreateView(generics.ListCreateAPIView):
    queryset = Service.objects.all().order_by('-date_created') 
    serializer_class = ServiceSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']
    parser_classes = (MultiPartParser, FormParser)
    def perform_create(self, serializer):
        # This is where the instance is saved
        serializer.save()

class AdminServiceRetrieveView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    lookup_field = 'id'

class AdminServiceUpdateView(generics.UpdateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    lookup_field = 'id'
    def put(self, request, *args, **kwargs):
        print(f"Received PUT request: {request.data}")
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            print(serializer.errors)  # Log serializer errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminServiceDeleteView(generics.DestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    lookup_field = 'id'

class ToggleServiceListing(APIView):
    def post(self, request, service_id):
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({'error': 'Service not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Toggle the is_listed field
        service.is_listed = not service.is_listed
        service.save()
        return Response({'message': 'Service listing status toggled successfully.'}, status=status.HTTP_200_OK)
class LatestCategoriesView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        # Fetch the latest 6 listed categories
        return Category.objects.filter(is_listed=True).order_by('-date_created')[:6]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
class AllCategoriesView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        # Fetch all listed categories
        return Category.objects.filter(is_listed=True).order_by('name')
class CategoryDetailView(generics.ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return Service.objects.filter(category_id=category_id, is_listed=True).order_by('-date_created')
