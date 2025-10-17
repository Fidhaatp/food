from django.urls import path, include
from . import views

app_name = 'web'

urlpatterns = [
    # Admin URLs - handled in main urls.py
    
    # Orders App URLs
    path('orders/', include('orders.urls', namespace='orders')),
    
    # Kitchen App URLs
    path('kitchen/', include('kitchen.urls', namespace='kitchen')),
    
    # Management App URLs
    path('management/', include('management.urls', namespace='management')),
    
    # Main landing page
    path('', views.landing_page, name='landing'),
]
