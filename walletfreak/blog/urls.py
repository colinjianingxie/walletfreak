from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('<str:slug>/', views.blog_detail, name='blog_detail'),
]
