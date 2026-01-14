from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('points-collection/', views.points_collection, name='points_collection'),
    path('add-card/<str:card_id>/', views.add_card, name='add_card'),
    path('update-status/<str:user_card_id>/', views.update_card_status, name='update_card_status'),
    path('remove-card/<str:user_card_id>/', views.remove_card, name='remove_card'),
    path('update-anniversary/<str:user_card_id>/', views.update_anniversary, name='update_anniversary'),
    path('toggle-benefit/<str:user_card_id>/<str:benefit_id>/', views.toggle_benefit_usage, name='toggle_benefit_usage'),
    path('update-benefit/<str:user_card_id>/<str:benefit_id>/', views.update_benefit_usage, name='update_benefit_usage'),
    path('toggle-ignore-benefit/<str:user_card_id>/<str:benefit_id>/', views.toggle_benefit_ignore_status, name='toggle_benefit_ignore_status'),
    
    # Loyalty Programs
    path('loyalty/add/', views.add_loyalty_program, name='add_loyalty_program'),
    path('loyalty/update/', views.update_loyalty_balance, name='update_loyalty_balance'),
    path('loyalty/remove/', views.remove_loyalty_program, name='remove_loyalty_program'),
    
    # Check delete consequences
    path('cards/check-delete/<str:user_card_id>/', views.check_card_delete_consequences, name='check_card_delete_consequences'),
    
    # Personality features
    path('personality/submit/', views.submit_personality_survey, name='submit_personality_survey'),

    path('personality/publish/', views.publish_personality, name='publish_personality'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
]
