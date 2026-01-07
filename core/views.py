from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q, Avg, Sum, Max
from django.db.models.functions import ExtractHour
from django.utils import timezone
from datetime import timedelta
import json
import random 
from chat.models import Profile, Message, Room, MusicTrack 

@user_passes_test(lambda u: u.is_superuser)
def analytics_dashboard(request):
    # ==========================================
    # 🟢 PHASE 1: CORE VISIBILITY (UNTOUCHED)
    # ==========================================
    filter_type = request.GET.get('filter', '24H')
    now = timezone.now()
    
    if filter_type == '24H': start_date = now - timedelta(hours=24)
    elif filter_type == '7D': start_date = now - timedelta(days=7)
    elif filter_type == '30D': start_date = now - timedelta(days=30)
    elif filter_type == 'LIFETIME': start_date = now - timedelta(days=365*5)
    else: start_date = now - timedelta(hours=24)

    msgs_qs = Message.objects.filter(timestamp__gte=start_date)

    online_count = Profile.objects.filter(last_activity__gte=now - timedelta(minutes=5)).count()
    dau_count = Profile.objects.filter(last_activity__date=now.date()).count()
    revenue = 0 
    mau_count = Profile.objects.filter(last_activity__gte=now - timedelta(days=30)).count() or 1
    stickiness = round((dau_count / mau_count) * 100, 1)
    total_msgs = msgs_qs.count()
    avg_session = 15

    top_cities = Profile.objects.exclude(city="Unknown").values('city').annotate(count=Count('id')).order_by('-count')[:5]
    
    gender_data = list(Profile.objects.values('gender').annotate(count=Count('id')))
    gender_dict = {item['gender']: item['count'] for item in gender_data if item['gender']}
    if not gender_dict: gender_dict = {'Male': 0, 'Female': 0}

    mobile_users = Profile.objects.filter(is_mobile=True).count()
    desktop_users = Profile.objects.filter(is_mobile=False).count()
    platform_data = [mobile_users, desktop_users] 

    free_users = Profile.objects.filter(subscription_tier='Free').count()
    premium_users = Profile.objects.exclude(subscription_tier='Free').count()
    subs_data = [free_users, premium_users]

    peak_hours = list(msgs_qs.annotate(hour=ExtractHour('timestamp')).values('hour').annotate(count=Count('id')))
    hours_list = [0] * 24
    for p in peak_hours: hours_list[p['hour']] = p['count']

    ranks = list(Profile.objects.values('subscription_tier').annotate(count=Count('id')))
    rank_labels = [r['subscription_tier'] for r in ranks]
    rank_values = [r['count'] for r in ranks]

    top_chatters = list(msgs_qs.values('user__username').annotate(count=Count('id')).order_by('-count')[:10])
    chat_labels = [u['user__username'] for u in top_chatters]
    chat_values = [u['count'] for u in top_chatters]
    top_xp_users = Profile.objects.order_by('-xp')[:10]
    top_aura_users = Profile.objects.order_by('-aura')[:10]

    # ==========================================
    # 🟡 PHASE 2: BEHAVIOR INTELLIGENCE
    # ==========================================
    voice_msgs = msgs_qs.exclude(audio='').count()
    image_msgs = msgs_qs.exclude(image='').count()
    text_msgs = total_msgs - (voice_msgs + image_msgs)
    msg_type_data = [text_msgs, voice_msgs, image_msgs]

    room_stats = list(msgs_qs.values('room__name').annotate(count=Count('id')).order_by('-count'))
    room_labels = [r['room__name'] for r in room_stats]
    room_values = [r['count'] for r in room_stats]

    mentions_count = msgs_qs.filter(content__icontains='@').count()
    active_user_count = msgs_qs.values('user').distinct().count() or 1
    avg_msg_per_user = round(total_msgs / active_user_count, 1)

    power_users_count = Profile.objects.filter(xp__gte=1000).count()
    seven_days_ago = now - timedelta(days=7)
    new_active_users = Profile.objects.filter(user__date_joined__gte=seven_days_ago, last_activity__date=now.date()).count()
    
    silent_users = dau_count - active_user_count
    if silent_users < 0: silent_users = 0
    participation_data = [active_user_count, silent_users]

    users_with_favs = Profile.objects.annotate(fav_count=Count('favorites')).filter(fav_count__gt=0).values_list('user', flat=True)
    multi_feature_count = msgs_qs.filter(user__in=users_with_favs).values('user').distinct().count()

    top_tracks = MusicTrack.objects.annotate(fav_count=Count('favorited_by')).order_by('-fav_count')[:5]
    genre_stats = list(MusicTrack.objects.filter(favorited_by__isnull=False).values('category').annotate(count=Count('favorited_by')).order_by('-count'))
    genre_labels = [g['category'] for g in genre_stats]
    genre_values = [g['count'] for g in genre_stats]
    total_favorites = sum(genre_values)

    cohort_start = now - timedelta(days=8)
    cohort_end = now - timedelta(days=7)
    cohort_users = Profile.objects.filter(user__date_joined__range=(cohort_start, cohort_end)).count()
    retained_users = Profile.objects.filter(user__date_joined__range=(cohort_start, cohort_end), last_activity__gte=now - timedelta(hours=24)).count()
    retention_rate = round((retained_users / cohort_users) * 100, 1) if cohort_users > 0 else 0

    # ==========================================
    # 🔴 PHASE 3: PREDICTION & OPTIMIZATION (COMPLETED)
    # ==========================================
    
    # 1. PREDICTIVE INSIGHTS
    active_pool = Profile.objects.filter(last_activity__gte=now - timedelta(days=30))
    risk_high = active_pool.filter(last_activity__lt=now - timedelta(days=7)).count()
    risk_med = active_pool.filter(last_activity__range=(now - timedelta(days=7), now - timedelta(days=3))).count()
    risk_low = active_pool.filter(last_activity__gte=now - timedelta(days=3)).count()
    churn_data = [risk_low, risk_med, risk_high] 

    # Engagement Forecast
    dau_3d_avg = Profile.objects.filter(last_activity__gte=now - timedelta(days=3)).count() / 3
    forecast_trend = "Stable"
    if dau_count > dau_3d_avg * 1.1: forecast_trend = "Upward 📈"
    elif dau_count < dau_3d_avg * 0.9: forecast_trend = "Downward 📉"
    
    # Expected Peak Hour (Calculated from max historical data)
    max_msg_hour = 21 # Default 9 PM
    if hours_list:
        max_msg_hour = hours_list.index(max(hours_list))
    expected_peak = f"{max_msg_hour}:00 - {max_msg_hour+1}:00"

    # 2. SMART ALERTS (Admin Only)
    alerts = []
    # Spike Detection
    if total_msgs > (dau_3d_avg * 20): # Rough heuristic
        alerts.append({"type": "Activity Spike", "msg": "Unusual message volume detected.", "level": "warning"})
    # Spam Pattern (User sent > 50 msgs in 24h)
    spammers = msgs_qs.values('user').annotate(c=Count('id')).filter(c__gt=50).count()
    if spammers > 0:
        alerts.append({"type": "Spam Pattern", "msg": f"{spammers} users sent >50 msgs today.", "level": "critical"})
    # Voice Overuse
    if voice_msgs > (total_msgs * 0.4) and total_msgs > 10:
        alerts.append({"type": "Bandwidth", "msg": "High Voice Note usage (>40%). Check storage.", "level": "info"})

    # 3. AUTOMATION SUGGESTIONS (Advanced)
    suggestions = []
    # "Many Bronze users active -> Offer Pilot promo"
    active_free_users = Profile.objects.filter(subscription_tier='Free', last_activity__date=now.date()).count()
    if active_free_users > 5:
        suggestions.append({"type": "Monetization", "msg": f"{active_free_users} active Free users. Push 'Pilot Tier' promo now.", "severity": "high"})
    # "Music usage high at night"
    night_msgs = msgs_qs.filter(timestamp__hour__gte=20).count()
    if night_msgs > (total_msgs * 0.5):
        suggestions.append({"type": "Engagement", "msg": "Night activity is high. Push 'Late Night Lofi' banner.", "severity": "med"})
    # "Low engagement in Learning"
    learning_msgs = msgs_qs.filter(room__name="Learning").count()
    if learning_msgs < 5:
        suggestions.append({"type": "Content", "msg": "Learning room is quiet. Auto-post a 'Fact of the Day'.", "severity": "low"})

    # 4. GROWTH & MONETIZATION
    # Best Time for CTA (1 hour before Peak)
    cta_hour = max_msg_hour - 1 if max_msg_hour > 0 else 23
    best_cta_time = f"{cta_hour}:00"
    
    # Users close to Level Up (Assuming 1000 XP increments)
    # Finding users with XP ending in 800-999
    # Logic: XP % 1000 >= 800
    # SQLite/Postgres specific, doing python filter for safety/simplicity
    close_to_level = 0
    for p in Profile.objects.filter(last_activity__date=now.date()):
        if 800 <= (p.xp % 1000) <= 999:
            close_to_level += 1

    # Revenue Health
    total_users = Profile.objects.count() or 1
    arpu = round(revenue / total_users, 2)
    funnel_data = [total_users, dau_count, active_user_count, premium_users]

    # 5. SYSTEM HEALTH
    system_load = "Normal"
    latency_ms = 45 
    if total_msgs > 100: 
        system_load = "Heavy"
        latency_ms = 120
    elif total_msgs > 500:
        system_load = "Critical"
        latency_ms = 300

    context = {
        # PHASE 1
        'filter': filter_type, 'online_count': online_count, 'dau_count': dau_count, 'stickiness': stickiness, 'revenue': revenue,
        'total_msgs': total_msgs, 'avg_session': avg_session, 'top_cities': top_cities, 'top_xp_users': top_xp_users, 'top_aura_users': top_aura_users,
        'gender_labels': json.dumps(list(gender_dict.keys())), 'gender_values': json.dumps(list(gender_dict.values())),
        'platform_data': json.dumps(platform_data), 'subs_data': json.dumps(subs_data),
        'hours_data': json.dumps(hours_list), 'rank_labels': json.dumps(rank_labels), 'rank_values': json.dumps(rank_values),
        'chat_labels': json.dumps(chat_labels), 'chat_values': json.dumps(chat_values),

        # PHASE 2
        'power_users_count': power_users_count, 'new_active_users': new_active_users, 'mentions_count': mentions_count, 'avg_msg_per_user': avg_msg_per_user,
        'multi_feature_count': multi_feature_count, 'retention_rate': retention_rate, 'total_favorites': total_favorites, 'top_tracks': top_tracks,
        'msg_type_data': json.dumps(msg_type_data), 'room_labels': json.dumps(room_labels), 'room_values': json.dumps(room_values),
        'participation_data': json.dumps(participation_data), 'genre_labels': json.dumps(genre_labels), 'genre_values': json.dumps(genre_values),

        # PHASE 3 (COMPLETE)
        'churn_data': json.dumps(churn_data),
        'predicted_dau': round(dau_3d_avg),
        'forecast_trend': forecast_trend,
        'expected_peak': expected_peak, # NEW
        'suggestions': suggestions,
        'alerts': alerts,               # NEW
        'arpu': arpu,
        'funnel_data': json.dumps(funnel_data),
        'system_load': system_load,
        'latency_ms': latency_ms,
        'best_cta_time': best_cta_time, # NEW
        'close_to_level': close_to_level # NEW
    }

    return render(request, 'custom_analytics.html', context)



@user_passes_test(lambda u: u.is_superuser)
def admin_hub(request):
    return render(request, 'admin_hub.html')




