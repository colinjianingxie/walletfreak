from django.urls import path
from . import views

urlpatterns = [
    path('', views.datapoint_list, name='datapoint_list'),
    path('submit/', views.submit_datapoint, name='submit_datapoint'),
    path('vote/<str:pk>/', views.vote_datapoint, name='vote_datapoint'),
    path('user/<str:uid>/wallet/', views.get_user_wallet, name='get_user_wallet'),
]
