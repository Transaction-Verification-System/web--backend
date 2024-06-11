import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        async_to_sync(self.channel_layer.group_add)(
            'chat_group', 
            self.channel_name
        )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'chat_group', 
            self.channel_name
        )

    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': message
        }))



