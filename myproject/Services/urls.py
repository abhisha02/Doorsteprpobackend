from django.urls import path
from .views import (
    AdminCategoryListCreateView,
    AdminCategoryRetrieveView,
    AdminCategoryUpdateView,
    AdminCategoryDeleteView,
    ToggleCategoryListing,
    AdminServiceListCreateView,
    AdminServiceRetrieveView,
    AdminServiceUpdateView,
    AdminServiceDeleteView,
    ToggleServiceListing,
    LatestCategoriesView,
    AllCategoriesView,
    CategoryDetailView
  
   
)

urlpatterns = [
    
    path('categories/', AdminCategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:id>/', AdminCategoryRetrieveView.as_view(), name='category-detail'),
    path('categories/update/<int:id>/', AdminCategoryUpdateView.as_view(), name='category-update'),  # Adjusted path
    path('categories/delete/<int:id>/', AdminCategoryDeleteView.as_view(), name='category-delete'),
    path('categories/toggle-listing/<int:category_id>/', ToggleCategoryListing.as_view(), name='toggle-category-listing'),
    path('latest-categories/', LatestCategoriesView.as_view(), name='latest-categories'),
    path('all-categories/', AllCategoriesView.as_view(), name='all-categories'),
     path('category/<int:category_id>/', CategoryDetailView.as_view(), name='category-detail'),

    

    #services
    path('services/', AdminServiceListCreateView.as_view(), name='service-list-create'),
    path('services/<int:id>/', AdminServiceRetrieveView.as_view(), name='service-detail'),
    path('services/update/<int:id>/', AdminServiceUpdateView.as_view(), name='service-update'),
    path('services/delete/<int:id>/', AdminServiceDeleteView.as_view(), name='service-delete'),
    path('services/toggle-listing/<int:service_id>/', ToggleServiceListing.as_view(), name='toggle-service-listing'),
]

