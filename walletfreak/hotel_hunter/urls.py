from django.urls import path
from . import views

app_name = 'hotel_hunter'

urlpatterns = [
    path('', views.index, name='index'),
    path('compare/', views.compare, name='compare'),
    path('history/', views.history, name='history'),
    path('report/<str:strategy_id>/', views.strategy_report, name='strategy_report'),
    path('report/<str:strategy_id>/prompt/', views.download_prompt, name='download_prompt'),
    path('api/status/', views.check_strategy_status, name='check_status'),
]
