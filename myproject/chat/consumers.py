# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from .models import ChatMessage
from Bookings.models import Booking
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

Customer = get_user_model()

class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f'user_{self.user_id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connected for user {self.user_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for user {self.user_id}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            else:
                print(f"Unknown message type: {message_type}")
        except json.JSONDecodeError:
            print(f"Invalid JSON: {text_data}")
        except Exception as e:
            print(f"Error in receive: {str(e)}")

    async def handle_chat_message(self, data):
        booking_id = data.get('booking_id')
        message = data.get('message')
        sender_id = data.get('sender_id')
        receiver_email = data.get('receiver_email')

        if not all([booking_id, message, sender_id, receiver_email]):
            print(f"Invalid chat message format: {data}")
            return

        try:
            booking = await self.get_booking(booking_id)
            sender = await self.get_user_by_id(sender_id)
            receiver = await self.get_user_by_email(receiver_email)

            chat_message = await self.save_chat_message(booking, sender, receiver, message)

            await self.channel_layer.group_send(
                f'user_{receiver.id}',
                {
                    'type': 'chat_message',
                    'booking_id': booking_id,
                    'message': message,
                    'sender_id': str(sender.id),
                    'sender_name': f'{sender.first_name} {sender.last_name}',
                    'timestamp': chat_message.timestamp.isoformat()
                }
            )
        except ObjectDoesNotExist as e:
            print(f"Object not found: {str(e)}")
        except ValueError as e:
            print(f"Invalid ID or email format: {str(e)}")
        except Exception as e:
            print(f"Error in handle_chat_message: {str(e)}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'booking_id': event['booking_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))

    @sync_to_async
    def get_booking(self, booking_id):
        return Booking.objects.get(id=booking_id)

    @sync_to_async
    def get_user_by_id(self, user_id):
        return Customer.objects.get(id=user_id)

    @sync_to_async
    def get_user_by_email(self, email):
        return Customer.objects.get(email=email)

    @sync_to_async
    def save_chat_message(self, booking, sender, receiver, message):
        chat_message = ChatMessage(
            booking=booking,
            sender=sender,
            receiver=receiver,
            message=message
        )
        chat_message.save()
        return chat_message
    async def booking_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'service_request_update',
            'booking': event['booking'],
            'is_new': True
        }))
    async def booking_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'booking_update',
            'booking': event['booking']
        }))
    async def booking_cancelled(self, event):
       await self.send(text_data=json.dumps({
            'type': 'booking_cancelled',
            'booking_id': event['booking_id']
        })) 
    async def temp_professional_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'temp_professional_update',
            'booking_id': event['booking_id'],
            'temp_professional': event['temp_professional']
        }))