from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json
from chat.models import Message, Profile, MusicTrack

User = get_user_model()

@user_passes_test(lambda u: u.is_staff)
def admin_analytics_dashboard(request):
    now = timezone.now()
    
    # --- 1. Filter Logic ---
    filter_type = request.GET.get('filter', '30')
    days = int(filter_type) if filter_type != 'all' else 3650
    start_date = now - timedelta(days=days)
    label_text = "Lifetime" if filter_type == 'all' else f"Last {days} Days"

    # --- 2. ONLINE USERS (Fix for '0 Online') ---
    # Logic: Anyone active in the last 5 minutes is "Online"
    online_threshold = now - timedelta(minutes=5)
    online_count = Profile.objects.filter(last_activity__gte=online_threshold).count()

    # --- 3. DAU / MAU (Growth) ---
    dau_count = Profile.objects.filter(last_activity__gte=now - timedelta(days=1)).count()
    mau_count = Profile.objects.filter(last_activity__gte=now - timedelta(days=30)).count()
    
    # Stickiness: How addictive is the app? (DAU/MAU)
    stickiness = round((dau_count / mau_count * 100), 1) if mau_count > 0 else 0

    # --- 4. SPONSORSHIP DATA (Cities & Gender) ---
    # Top Cities (Excluding 'Unknown' to keep list clean)
    city_stats = Profile.objects.exclude(city='Unknown')\
        .values('city').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Gender Split
    gender_stats = Profile.objects.values('gender').annotate(count=Count('id'))
    
    gender_labels = []
    gender_data = []
    for item in gender_stats:
        gender_labels.append(item['gender'])
        gender_data.append(item['count'])

    # --- 5. TOP TEXTERS ---
    top_texters = Message.objects.filter(timestamp__gte=start_date)\
        .values('user__username')\
        .annotate(msg_count=Count('id'))\
        .order_by('-msg_count')[:10]

    # --- 6. MUSIC STATS ---
    top_songs = MusicTrack.objects.annotate(likes=Count('favorited_by')).order_by('-likes')[:5]

    # --- 7. REVENUE ---
    premium_users = Profile.objects.exclude(subscription_tier='Free').count()
    # Assuming Rs. 1000 average per premium user
    total_revenue = premium_users * 1000 

    context = {
        'filter_label': label_text,
        'selected_filter': filter_type,
        
        # KPIs
        'online_count': online_count,
        'dau': dau_count,
        'mau': mau_count,
        'stickiness': stickiness,
        'total_revenue': f"{total_revenue:,}",
        'premium_users': premium_users,

        # JSON Data for Charts
        'city_labels': json.dumps([x['city'] for x in city_stats]),
        'city_data': json.dumps([x['count'] for x in city_stats]),
        'gender_labels': json.dumps(gender_labels),
        'gender_data': json.dumps(gender_data),
        'texter_labels': json.dumps([x['user__username'] for x in top_texters]),
        'texter_data': json.dumps([x['msg_count'] for x in top_texters]),
        
        # Raw Lists for Tables
        'top_songs': top_songs,
        'city_list': city_stats,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)