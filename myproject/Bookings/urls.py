from django.urls import path
from .views import AddToCartView, ClearCartView,CartView,CartItemUpdateView,CartItemDeleteView,CreateBookingView,RetrieveBookingView,UpdateBookingItemQuantityView,RemoveBookingItemView,AddressListCreateView,AddressUpdateView,AssignAddressToBookingView,AddressDeleteView,SelectSlotView,UpdateBookingStatusView,UserBookingsView,UpdateBookingStatusViewRescheduled,BookingDeleteView,ProBookingsRequestsView,ProfessionalAcceptBookingView,ProfessionalRejectBookingView,ProfessionalActiveTasksView,ProfessionalCancelBookingView,ProfessionalConfirmRescheduleView,TaskDoneView,PaymentReceivedView,CloseBookingView,UserBookingsReviewPageView,BookingReviewView,UserBookingsHistoryPageView,ProfessionalTasksHistoryView,FavouriteServicesView,ProfessionalAchievementView
urlpatterns = [
    #cart
    path('cart/add/<int:service_id>/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/clear/', ClearCartView.as_view(), name='clear-cart'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/item/<int:item_id>/', CartItemUpdateView.as_view(), name='update-cart-item'),
    path('cart/item/<int:item_id>/delete/', CartItemDeleteView.as_view(), name='delete-cart-item'),
    #booking
    path('create-booking/', CreateBookingView.as_view(), name='create-booking'),
    path('booking/<int:booking_id>/', RetrieveBookingView.as_view(), name='retrieve-booking'),
    path('booking-items/<int:booking_item_id>/update-quantity/', UpdateBookingItemQuantityView.as_view(), name='update_booking_item_quantity'),
    path('booking-items/<int:item_id>/delete', RemoveBookingItemView.as_view(), name='remove_booking_item'),
    #booking address
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressUpdateView.as_view(), name='address-update'),
    path('addresses/delete/<int:pk>/', AddressDeleteView.as_view(), name='address-delete'),
    #booking schedule
    path('bookings/<int:booking_id>/assign-address/', AssignAddressToBookingView.as_view(), name='assign-address'),
    path('bookings/select-slot/', SelectSlotView.as_view(), name='select-slot'),
    #booking status change
    path('bookings/booking/<int:booking_id>/update-status/', UpdateBookingStatusView.as_view(), name='update_booking_status'),
    path('bookings/user/', UserBookingsView.as_view(), name='user-bookings'),
    path('bookings/update-status-rescheduled/<int:booking_id>/', UpdateBookingStatusViewRescheduled.as_view(), name='update-booking-status-rescheduled'),
    path('bookings/<int:booking_id>/delete/', BookingDeleteView.as_view(), name='booking-delete'),
    path('professional/userrequests/', ProBookingsRequestsView.as_view(), name='professional-user-requests'),
    path('professional/accept/<int:booking_id>/', ProfessionalAcceptBookingView.as_view(), name='accept_booking'),
    path('professional/reject/<int:booking_id>/', ProfessionalRejectBookingView.as_view(), name='reject-booking'),
    path('professional/active-tasks/', ProfessionalActiveTasksView.as_view(), name='active-tasks'),
    path('professional/history-tasks/', ProfessionalTasksHistoryView.as_view(), name='history-tasks'),
    path('professional/cancel-booking/', ProfessionalCancelBookingView.as_view(), name='cancel_booking'),
    path('professional-confirm-reschedule/',ProfessionalConfirmRescheduleView.as_view(), name='confirm-reschedule-professional'),
    path('task-done/', TaskDoneView.as_view(), name='done-task'),
    path('payment-received/', PaymentReceivedView.as_view(), name='payment-received'),
    path('close-booking/', CloseBookingView.as_view(), name='close-booking'),
    path('user/reviewpage', UserBookingsReviewPageView.as_view(), name='user-bookings-review-page'),
    path('user/<int:pk>/review/', BookingReviewView.as_view(), name='booking-review'),
    path('user/history-page', UserBookingsHistoryPageView.as_view(), name='user-bookings-history-page'),
    path('user/favourite-services/', FavouriteServicesView.as_view(), name='favourite-services'),
    path('professional/achievements/', ProfessionalAchievementView.as_view(), name='professional-achievements'),
    

  
   

   
]
