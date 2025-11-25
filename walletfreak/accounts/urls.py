from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.firebase_login, name='firebase_login'),
    path('api/logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
]
