from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-card/<str:card_id>/', views.add_card, name='add_card'),
    path('update-status/<str:user_card_id>/', views.update_card_status, name='update_card_status'),
    path('remove-card/<str:user_card_id>/', views.remove_card, name='remove_card'),
    path('update-anniversary/<str:user_card_id>/', views.update_anniversary, name='update_anniversary'),
]
