from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('cards/', views.admin_card_list, name='admin_card_list'),
    path('cards/create/', views.admin_card_create, name='admin_card_create'),
    path('cards/<str:card_id>/edit/', views.admin_card_edit, name='admin_card_edit'),
    path('cards/<str:card_id>/delete/', views.admin_card_delete, name='admin_card_delete'),
    path('personalities/', views.admin_personality_list, name='admin_personality_list'),
    path('users/', views.admin_user_list, name='admin_user_list'),
    path('users/<str:uid>/toggle-super/', views.toggle_super_staff, name='toggle_super_staff'),
    path('users/<str:uid>/toggle-editor/', views.toggle_editor, name='toggle_editor'),
    # Blog management URLs
    path('blogs/', views.admin_blog_list, name='admin_blog_list'),
    path('blogs/create/', views.admin_blog_create, name='admin_blog_create'),
    path('blogs/<str:blog_id>/edit/', views.admin_blog_edit, name='admin_blog_edit'),
    path('blogs/<str:blog_id>/delete/', views.admin_blog_delete, name='admin_blog_delete'),
    path('blogs/<str:blog_id>/publish/', views.admin_blog_publish, name='admin_blog_publish'),
]
