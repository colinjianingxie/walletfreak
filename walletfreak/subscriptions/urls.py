from django.urls import path
from . import views

urlpatterns = [
    path('', views.subscription_home, name='subscription_home'),
    path('checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('portal/', views.create_portal_session, name='create_portal_session'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.success, name='subscription_success'),
    path('cancel/', views.cancel, name='subscription_cancel'),
]
