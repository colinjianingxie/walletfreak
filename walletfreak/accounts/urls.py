from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.firebase_login, name='firebase_login'),
    path('api/logout/', views.logout_view, name='logout'),
    path('api/update-notifications/', views.ajax_update_notifications, name='update_notifications'),
    path('api/sync-profile/', views.ajax_sync_profile, name='sync_profile'),
    path('auth/action/', views.auth_action, name='auth_action'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
]
