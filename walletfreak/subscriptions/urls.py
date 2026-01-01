from django.urls import path
from . import views

urlpatterns = [
    path('pricing/', views.pricing_page, name='pricing_page'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.success, name='subscription_success'),
    path('cancel/', views.cancel, name='subscription_cancel'),
]
