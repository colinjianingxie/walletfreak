from django.urls import path
from . import views
from . import media_views

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('drafts/', views.blog_drafts, name='blog_drafts'),
    path('manage-status/', views.blog_manage_status, name='blog_manage_status'),
    path('media/', media_views.media_library, name='media_library'),
    path('media/upload/', media_views.upload_media, name='upload_media'),
    path('media/<str:asset_id>/delete/', media_views.delete_media, name='delete_media'),
    path('create/', views.blog_create, name='blog_create'),
    path('<str:slug>/', views.blog_detail, name='blog_detail'),
    path('<str:slug>/edit/', views.blog_edit, name='blog_edit'),
    path('<str:slug>/delete/', views.blog_delete, name='blog_delete'),
    path('api/<str:blog_id>/status/', views.blog_quick_status_change, name='blog_quick_status_change'),
]

