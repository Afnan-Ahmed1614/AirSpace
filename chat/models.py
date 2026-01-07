from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date


# 1. TRACKS LONG TERM HABITS
class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak_data')
    current_streak = models.IntegerField(default=0)
    highest_streak = models.IntegerField(default=0)
    last_action_date = models.DateField(null=True, blank=True) # Date they last kept streak alive
    
    # Recovery Logic
    is_frozen = models.BooleanField(default=False) # If they missed a day but are within 24h recovery window
    recovery_ads_watched = models.IntegerField(default=0) # Needs 3 to recover

    def __str__(self): return f"{self.user.username} - {self.current_streak} Days"

# 2. TRACKS DAILY LIMITS (Resets effectively by creating new row per day)
class DailyActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_activities')
    date = models.DateField(default=timezone.now)
    
    # Login Bonus
    login_claimed = models.BooleanField(default=False)
    
    # Message Bonus
    messages_sent_today = models.IntegerField(default=0)
    msg_bonus_claimed = models.BooleanField(default=False)
    
    # Aura Logic
    first_like_received = models.BooleanField(default=False)
    
    # Ads Logic
    xp_ads_watched = models.IntegerField(default=0)   # Limit 5
    aura_ads_watched = models.IntegerField(default=0) # Limit 7
    booster_claimed = models.BooleanField(default=False) # Limit 1

    class Meta:
        unique_together = ('user', 'date') # Ensures one row per user per day
        
        

class MusicTrack(models.Model):
    CATEGORY_CHOICES = [
        ('love', 'Love / Romantic'),
        ('sad', 'Sad / Heartbreak'),
        ('peaceful', 'Peaceful / Healing'),
        ('travel', 'Travel / Vibe'),
        ('mashup', 'Mashups / Remix'),
    ]
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)
    audio_url = models.URLField(max_length=500) 
    cover_image = models.ImageField(upload_to='music_covers/', null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='love')
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.title} - {self.artist}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=50, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    xp = models.IntegerField(default=0)
    aura = models.IntegerField(default=0)
    current_theme = models.CharField(max_length=50, default="soft-glass") 
    subscription_tier = models.CharField(max_length=50, default="Free")
    favorites = models.ManyToManyField(MusicTrack, related_name='favorited_by', blank=True)
    # Stores "Rawalpindi", "Lahore", etc. automatically
    city = models.CharField(max_length=100, default="Unknown") 
    #device check.
    is_mobile = models.BooleanField(default=False)
    
    # You must set this manually or via a form later
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default="Male")
    
    # Tracks exactly when they were last clicking links
    last_activity = models.DateTimeField(default=timezone.now)
    def __str__(self): return self.user.username
    def get_tier_data(self):
        tiers = [("LEGEND", 500000), ("CONQUEROR", 200000), ("DOMINATOR", 100000), ("MASTER", 50000), ("ACE", 25000), ("CROWN", 10000), ("DIAMOND", 5000), ("PLATINUM", 1000), ("GOLD", 100), ("BRONZE", 0)]
        for name, threshold in tiers:
            if self.xp >= threshold: return {"name": name, "full": name, "next_xp": 100 if name=="BRONZE" else "MAX", "progress": 100}
        return {"name": "BRONZE", "full": "BRONZE", "next_xp": 100, "progress": self.xp}
    def get_tier(self): return self.get_tier_data()['full']

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    audio = models.FileField(upload_to='chat_audio/', null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_messages', blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    is_deleted = models.BooleanField(default=False)
    hidden_by = models.ManyToManyField(User, related_name='hidden_messages', blank=True)
    def __str__(self): return f"{self.user.username}: {self.content[:20]}"

class MusicSuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song_name = models.CharField(max_length=100); artist_name = models.CharField(max_length=100); link = models.URLField(max_length=500); timestamp = models.DateTimeField(auto_now_add=True)

class SiteConfig(models.Model):
    site_name = models.CharField(max_length=50, default="AirSpace")
    xp_per_message = models.IntegerField(default=10)
    aura_per_like = models.IntegerField(default=15)
    aura_per_dislike = models.IntegerField(default=10)
    announcement_min_xp = models.IntegerField(default=500)
    subscription_packages = models.JSONField(default=dict) 
    default_track = models.ForeignKey(MusicTrack, null=True, blank=True, on_delete=models.SET_NULL)
    # Retention Configs
    daily_login_xp = models.IntegerField(default=5)
    daily_msg_bonus_xp = models.IntegerField(default=19)
    streak_recover_cost = models.IntegerField(default=3) # Ads needed
    streak_bonus_7_day = models.IntegerField(default=500)  # Configurable Reward
    streak_bonus_30_day = models.IntegerField(default=2000)
    def save(self, *args, **kwargs): self.pk = 1; super(SiteConfig, self).save(*args, **kwargs)
    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        if created: obj.subscription_packages = {"Pilot": {"price": 100, "xp_mult": 2}, "Ace": {"price": 250, "xp_mult": 3}, "Commander": {"price": 500, "xp_mult": 4}}; obj.save()
        return obj

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance, display_name=instance.username)
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try: instance.profile.save()
    except Profile.DoesNotExist: Profile.objects.create(user=instance, display_name=instance.username)