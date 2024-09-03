from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from Bookings.models import Booking

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            if request.user != booking.customer and request.user != booking.professional:
                return Response({"error": "You don't have permission to view this chat."}, status=status.HTTP_403_FORBIDDEN)
           
            messages = ChatMessage.objects.filter(booking_id=booking_id).order_by('timestamp')
            serializer = ChatMessageSerializer(messages, many=True)
           
            # Add isSentByCurrentUser field to each message
            data = serializer.data
            for message in data:
                message['isSentByCurrentUser'] = message['sender_id'] == request.user.id
           
            return Response(data, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)