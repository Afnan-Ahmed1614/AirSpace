from django.urls import path
from . import views
from core.views import analytics_dashboard
from core.views import analytics_dashboard, admin_hub

urlpatterns = [
    # Core
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    
    # App
    path('profile/', views.profile_view, name='profile'),
    path('membership/', views.membership_view, name='membership'),
    path('chat/<str:room_name>/', views.room, name='room'),
    
    # Logic
    path('vote/<int:message_id>/<str:vote_type>/', views.vote_message, name='vote_message'),
    
    # Admin / God Mode
    path('control-tower/', views.admin_dashboard, name='admin_dashboard'),
    path('update-settings/', views.update_settings, name='update_settings'),
    path('god-mode-action/', views.god_mode_action, name='god_mode_action'),
    path('clear-all-chats/', views.clear_all_chats, name='clear_all_chats'),
    path('manage-packages/', views.manage_packages, name='manage_packages'),
    
    # Music Logic
    path('manage-music/', views.manage_music, name='manage_music'),
    
    # --- NEW URLS ---
    path('toggle-fav/<int:track_id>/', views.toggle_music_fav, name='toggle_music_fav'),
    path('suggest-music/', views.suggest_music, name='suggest_music'),
    path('delete-suggestion/<int:suggestion_id>/', views.delete_suggestion, name='delete_suggestion'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('clear-all-chats/', views.clear_all_chats, name='clear_all_chats'),
    
    
    
    path('super-dashboard/', analytics_dashboard, name='super_dashboard'),
    path('admin-hub/', admin_hub, name='admin_hub'),
    path('ads/claim/<str:ad_type>/', views.claim_ad_reward, name='claim_ad'),
]