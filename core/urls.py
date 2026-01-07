from django.urls import path
from . import views  # Make sure views imported hai
from core.views import analytics_dashboard

urlpatterns = [
    # ... Baki purane links yahan honge (control-tower waghaira) ...

    # 👇 YEH LINE ADD KARO
    path('super-dashboard/', views.analytics_dashboard, name='super_dashboard'),
]