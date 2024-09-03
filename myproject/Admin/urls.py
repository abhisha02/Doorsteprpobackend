from django.urls import path
from . import views
from .views import ApproveProfessionalView,RejectProfessionalView,AdminBookingsListCreateView,AdminDashboardDataView





urlpatterns = [
  
   path('users/', views.AdminUserListCreateView.as_view(), name='admin-user-list-create'), 
   path('users/<int:id>/', views.AdminUserRetrieveView.as_view(), name='admin-user-list-single'),
   path('users/update/<int:id>/', views.AdminUserUpdateView.as_view(), name='admin-user-list-single-update'),
   path('users/delete/<int:id>/', views.AdminUserDeleteView.as_view(), name='admin-user-list-single-delete'),

  #Professionals
   path('professionals/', views.AdminProfessionalListCreateView.as_view(), name='admin-professionals-list-create'), 
   path('professionals/<int:id>/', views.AdminProfessionalRetrieveView.as_view(), name='admin-professionals-list-single'),
   path('professionals/update/<int:id>/', views.AdminProfessionalUpdateView.as_view(), name='admin-professionals-list-single-update'),
   path('professionals/delete/<int:id>/', views.AdminProfessionalDeactivateActivateView.as_view(), name='admin-professionals-list-single-delete'),
   path('professionals/approve/<int:id>/', ApproveProfessionalView.as_view(), name='approve_professional'),
   path('professionals/reject/<int:id>/', RejectProfessionalView.as_view(), name='reject_professional'),
   path('bookings-list/',AdminBookingsListCreateView.as_view(), name='admin-booking-list'),
   path('admin-dashboard-data/', AdminDashboardDataView.as_view(), name='admin_dashboard_data'),

   
 
]