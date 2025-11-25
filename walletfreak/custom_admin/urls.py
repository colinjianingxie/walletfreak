from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('cards/', views.admin_card_list, name='admin_card_list'),
    path('personalities/', views.admin_personality_list, name='admin_personality_list'),
    path('users/', views.admin_user_list, name='admin_user_list'),
    path('users/<str:uid>/toggle-super/', views.toggle_super_staff, name='toggle_super_staff'),
]
