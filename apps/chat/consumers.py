import json
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chat.models import Chat, Rooms


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connect to a channel"""
        self.user = self.scope['user']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_{}'.format(self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from a channel"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Reveice a chat message into a channel"""
        if self.user and not self.user.is_authenticated:
            return

        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        full_name = "{} {}".format(self.user.first_name, self.user.last_name)
        if full_name == " ":
            full_name = "--"

        try:
            room = Rooms.objects.get(name=self.room_name)
        except Rooms.DoesNotExist:
            return

        chat_object = Chat.objects.create(user_id=self.user.id, message=message, room=room)

        created_at = chat_object.created_at.strftime('%H:%M:%S %Y/%m/%d')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': "chat_message",
                'message': message,
                'user_id': self.user.id,
                'publisher_full_name': full_name,
                'created_at': created_at,
            }
        )

    async def chat_message(self, event):
        """Send the chat message to the channnel"""
        if self.user and not self.user.is_authenticated:
            return

        user_id = event['user_id']
        message = event['message']
        created_at = event['created_at']
        publisher_full_name = event['publisher_full_name']

        await self.send(text_data=json.dumps({
            'user_id': user_id,
            'created_at': created_at,
            'message': "{}".format(message),
            'publisher_full_name': publisher_full_name,
        }))
