from .models import SiteConfig, MusicTrack, Profile, UserStreak, DailyActivity
from .retention_engine import get_streak_multiplier
from django.utils import timezone
import json

def global_config(request):
    return {'config': SiteConfig.get_solo()}

def layout_data(request):
    config = SiteConfig.get_solo()
    tracks = MusicTrack.objects.all().order_by('-timestamp')
    
    # NEW CATEGORIES MAP
    library = { 'love': [], 'sad': [], 'peaceful': [], 'travel': [], 'mashup': [], 'favorites': [] }
    
    fav_ids = []
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            fav_tracks = profile.favorites.all()
            for t in fav_tracks:
                fav_ids.append(t.id)
                library['favorites'].append({'id': t.id, 'title': t.title, 'artist': t.artist, 'url': t.audio_url, 'cover': t.cover_image.url if t.cover_image else ''})
        except: pass

    for t in tracks:
        track_data = {'id': t.id, 'title': t.title, 'artist': t.artist, 'url': t.audio_url, 'cover': t.cover_image.url if t.cover_image else ''}
        if t.category in library:
            library[t.category].append(track_data)
            
    counts = {k: len(v) for k, v in library.items()}
    default_song = None
    if config.default_track:
        default_song = {'id': config.default_track.id, 'title': config.default_track.title, 'artist': config.default_track.artist, 'url': config.default_track.audio_url, 'category': config.default_track.category}

    return {
        'config': config,
        'music_library': json.dumps(library),
        'playlist_counts': counts,
        'default_music': json.dumps(default_song),
        'fav_ids': json.dumps(fav_ids)
    }

# --- 🔥 NEW ADDITION: RETENTION METRICS ---
def retention_metrics(request):
    """
    Makes 'streak_multiplier' and daily status available in ALL templates globally.
    """
    if not request.user.is_authenticated:
        return {'streak_multiplier': 1.0}

    try:
        # 1. Get Base Multiplier from Streak
        streak, _ = UserStreak.objects.get_or_create(user=request.user)
        multiplier = get_streak_multiplier(streak.current_streak)

        # 2. Check for Daily Booster (Add 0.5x if active)
        today = timezone.now().date()
        # We use filter().first() to avoid creating a row if it doesn't exist just for reading
        daily = DailyActivity.objects.filter(user=request.user, date=today).first()
        
        if daily and daily.booster_claimed:
            multiplier += 0.5

        return {
            'streak_multiplier': round(multiplier, 1)
        }
    except Exception:
        # Fallback in case of DB migration issues or errors
        return {'streak_multiplier': 1.0}