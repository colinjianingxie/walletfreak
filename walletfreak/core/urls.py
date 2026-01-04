from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('features/', views.features, name='features'),
    path('contact/', views.contact, name='contact'),
    path('api/get-firebase-token/', views.get_firebase_token, name='get_firebase_token'),
    
    # Cron Jobs
    path('cron/email-notifications/', views.run_notification_cron, name='cron_email'),
    path('cron/email-cleanup/', views.run_cleanup_cron, name='cron_cleanup'),
    
    # Pricing
    path('pricing/', views.pricing, name='pricing'),
    
    # Legal
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
]
