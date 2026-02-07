from django.urls import path
from . import views

app_name = 'award_scout'

urlpatterns = [
    path('', views.index, name='index'),
    path('track/', views.track_selected, name='track'),
]
