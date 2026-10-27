# demografia/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('comparativo/', views.dashboard_comparativo_view, name='dashboard_comparativo'),
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),
    path('api/dashboard-comparativo/', views.api_dashboard_comparativo, name='api_dashboard_comparativo'),
]