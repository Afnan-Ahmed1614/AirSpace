from django.contrib import admin
from .models import Profile, Room, Message, SiteConfig, MusicTrack

admin.site.register(Profile)
admin.site.register(Room)
admin.site.register(Message)
admin.site.register(SiteConfig)
admin.site.register(MusicTrack)