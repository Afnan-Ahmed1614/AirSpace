import requests
from django.utils import timezone
from django.core.cache import cache
from .models import Profile, DailyActivity  # DailyActivity add kiya
from .retention_engine import grant_xp      # XP Engine add kiya

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # CACHE CHECK: Database par load kam karne ke liye (Every 60 seconds)
            cache_key = f"last_seen_{request.user.id}"
            
            if not cache.get(cache_key):
                try:
                    # --- PART 1: PROFILE UPDATES (Existing) ---
                    profile = request.user.profile
                    
                    # 1. Update Time
                    profile.last_activity = timezone.now()
                    
                    # 2. DEVICE DETECTION
                    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
                    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
                    profile.is_mobile = is_mobile

                    # 3. CITY DETECTION
                    if profile.city == "Unknown" or not profile.city:
                        ip = request.META.get('REMOTE_ADDR')
                        
                        # Localhost Fix
                        if ip == '127.0.0.1': 
                            profile.city = "Rawalpindi (Local)"
                        else:
                            try:
                                response = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
                                data = response.json()
                                if data.get('status') == 'success':
                                    profile.city = data.get('city', 'Unknown')
                            except:
                                pass 

                    # Save Profile Changes
                    profile.save()

                    # --- PART 2: DAILY LOGIN BONUS (NEW) ---
                    # Hum isay bhi cache block mein rakhenge taake har second DB check na ho
                    today = timezone.now().date()
                    
                    # Check/Create today's activity row
                    daily, created = DailyActivity.objects.get_or_create(
                        user=request.user, 
                        date=today
                    )
                    
                    # Agar aaj ka bonus nahi mila, to de do
                    if not daily.login_claimed:
                        grant_xp(request.user, 5, source="Daily Login")
                        daily.login_claimed = True
                        daily.save()
                    
                    # Cache set kar do 60 seconds ke liye (Profile + Bonus checks won't run again for 1 min)
                    cache.set(cache_key, True, 60) 

                except Exception as e:
                    # Agar koi error aaye to print karo magar site crash na ho
                    print(f"Middleware Error: {e}")
                    pass

        response = self.get_response(request)
        return response