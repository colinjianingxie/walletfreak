from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('wallet/', views.wallet, name='wallet'),
    path('add-card/<str:card_id>/', views.add_card, name='add_card'),
    path('update-status/<str:user_card_id>/', views.update_card_status, name='update_card_status'),
    path('remove-card/<str:user_card_id>/', views.remove_card, name='remove_card'),
    path('update-anniversary/<str:user_card_id>/', views.update_anniversary, name='update_anniversary'),
    path('toggle-benefit/<str:user_card_id>/<str:benefit_id>/', views.toggle_benefit_usage, name='toggle_benefit_usage'),
    path('update-benefit/<str:user_card_id>/<str:benefit_id>/', views.update_benefit_usage, name='update_benefit_usage'),
]
