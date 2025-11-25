from django.urls import path
from . import views

urlpatterns = [
    path('personalities/', views.personality_list, name='personality_list'),
    path('personalities/<str:personality_id>/', views.personality_detail, name='personality_detail'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/<str:card_id>/', views.card_detail, name='card_detail'),
]
