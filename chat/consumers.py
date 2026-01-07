import json
import base64
from django.core.files.base import ContentFile
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Message, Room, Profile, SiteConfig

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get('command')

            if command == 'new_message':
                msg_data = await self.save_message(data)
                if msg_data:
                    await self.channel_layer.group_send(self.room_group_name, {'type': 'chat_message', 'message_data': msg_data})
            
            elif command == 'delete_me':
                await self.delete_message_db(data['msg_id'], 'me')
            
            elif command == 'delete_everyone':
                if await self.delete_message_db(data['msg_id'], 'everyone'):
                    await self.channel_layer.group_send(self.room_group_name, {'type': 'message_deleted', 'msg_id': data['msg_id']})

            elif command == 'edit_message':
                if await self.edit_message_db(data['msg_id'], data['new_content']):
                    await self.channel_layer.group_send(self.room_group_name, {'type': 'message_edited', 'msg_id': data['msg_id'], 'new_content': data['new_content']})

            # Add this block inside receive() method
            elif command == 'clear_history':
                await self.clear_history_for_user()
                await self.send(text_data=json.dumps({'type': 'history_cleared'}))

        except Exception as e:
            print(f"WS Error: {e}")

    async def chat_message(self, event): await self.send(text_data=json.dumps({'type': 'chat_message', **event['message_data']}))
    async def message_deleted(self, event): await self.send(text_data=json.dumps(event))
    async def message_edited(self, event): await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, data):
        user = self.scope["user"]
        if not user.is_authenticated: return None
        room, _ = Room.objects.get_or_create(name=self.room_name)
        profile, _ = Profile.objects.get_or_create(user=user)
        
        content = data.get('message', '')
        image_data = data.get('image'); audio_data = data.get('audio'); reply_id = data.get('reply_id')

        if not content and not image_data and not audio_data: return None

        new_msg = Message(user=user, room=room, content=content)
        if reply_id:
            try: new_msg.reply_to = Message.objects.get(id=reply_id)
            except: pass

        if image_data:
            try:
                fmt, imgstr = image_data.split(';base64,'); ext = fmt.split('/')[-1]
                new_msg.image.save(f"img_{user.id}_{int(timezone.now().timestamp())}.{ext}", ContentFile(base64.b64decode(imgstr)), save=False)
            except: pass
        
        if audio_data:
            try:
                if "base64," in audio_data: fmt, audiostr = audio_data.split(';base64,')
                else: audiostr = audio_data
                new_msg.audio.save(f"voice_{user.id}_{int(timezone.now().timestamp())}.webm", ContentFile(base64.b64decode(audiostr)), save=False)
            except: pass

        new_msg.save()
        
        try:
            config = SiteConfig.get_solo(); profile.xp += config.xp_per_message
        except: profile.xp += 2
        profile.save()

        return {
            'id': new_msg.id, 'username': user.username, 'message': new_msg.content, 'tier': profile.get_tier(), 'aura': profile.aura,
            'timestamp': timezone.now().strftime('%H:%M'), 'image_url': new_msg.image.url if new_msg.image else None,
            'audio_url': new_msg.audio.url if new_msg.audio else None, 'user_avatar': profile.profile_picture.url if profile.profile_picture else None,
            'reply_context': {'username': new_msg.reply_to.user.username, 'message': new_msg.reply_to.content} if new_msg.reply_to else None,
            'likes': 0, 'dislikes': 0
        }

    @database_sync_to_async
    def delete_message_db(self, msg_id, type):
        try:
            msg = Message.objects.get(id=msg_id)
            user = self.scope['user']
            if type == 'everyone' and (msg.user == user or user.is_staff):
                msg.is_deleted = True; msg.content = "🚫 Message deleted"; msg.image = None; msg.audio = None; msg.save(); return True
            elif type == 'me':
                msg.hidden_by.add(user); msg.save(); return True
        except: return False

    @database_sync_to_async
    def edit_message_db(self, msg_id, new_text):
        try:
            msg = Message.objects.get(id=msg_id, user=self.scope['user'])
            if not msg.is_deleted: msg.content = new_text; msg.save(); return True
        except: return False

    @database_sync_to_async
    def clear_history_for_user(self):
        user = self.scope['user']; room = Room.objects.get(name=self.room_name)
        messages = Message.objects.filter(room=room)
        for m in messages: m.hidden_by.add(user)