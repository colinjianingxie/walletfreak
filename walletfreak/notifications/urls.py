from django.urls import path
from . import views

urlpatterns = [
    path('api/get/', views.get_notifications, name='get_notifications'),
    path('api/mark-read/', views.mark_read, name='mark_notifications_read'),
    path('settings/notifications/', views.history_view, name='notifications_history'),
]
