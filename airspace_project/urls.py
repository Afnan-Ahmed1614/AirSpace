from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from chat import views as chat_views
from core.views_analytics import admin_analytics_dashboard
from django.views.generic.base import RedirectView  # 👈 YEH MISSING HAI

urlpatterns = [
    path('admin/analytics/', admin_analytics_dashboard, name='admin_analytics'),
    path('admin/', admin.site.urls),
    
    # Your Chat App
    path('chat/', include('chat.urls')), 
    
    # Redirect root to Chat
    path('', chat_views.home, name='root_home'), 
    path('', include('chat.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/images/logo.png', permanent=True)),
    
 
    
  
]

# --- THIS IS THE MAGIC PART ---
# It tells Django: "If a URL starts with /media/, look in the media folder"
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)