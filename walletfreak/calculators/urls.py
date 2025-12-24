from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='calculators_index'),
    path('worth-it/', views.worth_it_list, name='worth_it_list'),
    path('worth-it/<slug:card_slug>/', views.worth_it_audit, name='worth_it_audit'),
    path('worth-it/<slug:card_slug>/calculate/', views.worth_it_calculate, name='worth_it_calculate'),
    path('optimizer/', views.optimizer_input, name='optimizer_input'),
    path('optimizer/calculate/', views.optimizer_calculate, name='optimizer_calculate'),
]
