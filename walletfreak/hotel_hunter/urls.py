from django.urls import path
from . import views

app_name = 'hotel_hunter'

urlpatterns = [
    path('', views.index, name='index'),
]
