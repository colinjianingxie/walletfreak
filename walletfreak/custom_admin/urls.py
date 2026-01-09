from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('cards/', views.admin_card_list, name='admin_card_list'),
    path('cards/<str:card_id>/edit/', views.admin_card_edit, name='admin_card_edit'),
    path('cards/<str:card_id>/generate-prompt/', views.admin_generate_prompt, name='admin_generate_prompt'),
    path('cards/<str:card_id>/run-update/', views.admin_run_grok_update, name='admin_run_grok_update'),
    path('cards/generate-bulk-prompt/', views.admin_generate_bulk_prompt, name='admin_generate_bulk_prompt'),
    path('cards/generate-new-prompt/', views.admin_generate_new_prompt, name='admin_generate_new_prompt'),
    path('cards/save-card-json/', views.admin_save_card_json, name='admin_save_card_json'),
]
