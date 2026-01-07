from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import re
from .models import Message 

# --- NEW IMPORTS (RETENTION ENGINE) ---
from .retention_engine import get_or_create_daily, update_streak, grant_xp

User = get_user_model()

# ==========================================
# 1. OLD FEATURE: MENTIONS NOTIFICATION (UNTOUCHED)
# ==========================================
@receiver(post_save, sender=Message)
def check_mentions(sender, instance, created, **kwargs):
    if created:
        content = instance.content
        # Regex to find @username
        mentions = re.findall(r'@(\w+)', content)
        
        if mentions:
            channel_layer = get_channel_layer()
            sender_name = instance.user.username
            
            for username in mentions:
                try:
                    target_user = User.objects.get(username=username)
                    # We assume users listen to a group named 'user_{id}'
                    # If your auth system uses a different group name, adjust here.
                    group_name = f"user_{target_user.id}"
                    
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            "type": "send_notification",
                            "message": f"@{sender_name} mentioned you!",
                            "sender": sender_name
                        }
                    )
                except User.DoesNotExist:
                    continue

# ==========================================
# 2. NEW FEATURE: DAILY XP & STREAKS (APPENDED)
# ==========================================
@receiver(post_save, sender=Message)
def track_user_activity(sender, instance, created, **kwargs):
    """
    Tracks streaks and daily message limits safely via Signals.
    Works for both HTTP and WebSocket messages.
    """
    if created and instance.user:
        user = instance.user
        
        # A. Streak Update (Logic: Logged in + Sent Message = Streak Kept)
        update_streak(user)
        
        # B. Daily Message Count & Bonus Logic
        daily = get_or_create_daily(user)
        daily.messages_sent_today += 1
        
        # Check Bonus (Target: 5 Messages)
        if daily.messages_sent_today == 5 and not daily.msg_bonus_claimed:
            grant_xp(user, 19, source="Daily Msg Bonus")
            daily.msg_bonus_claimed = True
            
        daily.save()