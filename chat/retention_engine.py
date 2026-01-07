from django.utils import timezone
from .models import UserStreak, DailyActivity, Profile
from decimal import Decimal
from .models import SiteConfig

# --- MULTIPLIER LOGIC ---
def get_streak_multiplier(days):
    """ Calculates non-linear multiplier based on streak days """
    if days <= 1: return 1.0
    
    # Hardcoded progression for first 10 days
    progression = {
        2: 1.5, 3: 1.8, 4: 2.0, 5: 2.1, 
        6: 2.2, 7: 2.4, 8: 2.5, 9: 2.6, 10: 2.7
    }
    
    if days in progression:
        return progression[days]
    
    # Cap at 30 days logic (Example: max 3.5x)
    if days > 10:
        extra = (days - 10) * 0.05
        return min(2.7 + extra, 3.5) # Capped at 3.5x
    
    return 1.0

# --- CORE UTILS ---
def get_or_create_daily(user):
    """ Get today's tracking row """
    today = timezone.now().date()
    daily, created = DailyActivity.objects.get_or_create(user=user, date=today)
    return daily

def update_streak(user):
    """ Call this when user sends a message (The trigger for keeping streak) """
    streak, _ = UserStreak.objects.get_or_create(user=user)
    today = timezone.now().date()
    
    if streak.last_action_date == today:
        return # Already counted today
    
    # Check logic
    if streak.last_action_date:
        delta = (today - streak.last_action_date).days
        if delta == 1:
            # Consecutive day - Increment
            streak.current_streak += 1
            
            # 🔥 NEW: CHECK FOR MILESTONE REWARDS
            config = SiteConfig.get_solo()
            
            if streak.current_streak == 7:
                grant_xp(user, config.streak_bonus_7_day, source="🔥 7-Day Streak Bonus")
            
            elif streak.current_streak == 30:
                grant_xp(user, config.streak_bonus_30_day, source="🔥🔥 30-Day Legend Bonus")
                # Optional: Add Aura too if you want
                user.profile.aura += 100 
                user.profile.save()

        elif delta > 1:
            # Streak Broken
            streak.current_streak = 1 
    else:
        streak.current_streak = 1 # First time ever
        
    streak.last_action_date = today
    if streak.current_streak > streak.highest_streak:
        streak.highest_streak = streak.current_streak
    streak.save()

# --- REWARD FUNCTIONS ---
def grant_xp(user, amount, source="Action"):
    """ Safe XP Granting with Multiplier """
    profile = user.profile
    streak, _ = UserStreak.objects.get_or_create(user=user)
    
    # Apply Multiplier
    mult = get_streak_multiplier(streak.current_streak)
    
    # Check for Daily Booster Ad
    daily = get_or_create_daily(user)
    if daily.booster_claimed:
        mult += 0.5 # Add 1.5x effect
        
    final_xp = int(amount * mult)
    
    profile.xp += final_xp
    profile.save()
    return final_xp