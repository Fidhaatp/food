from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.kitchen_login, name='login'),
    path('logout/', views.kitchen_logout, name='logout'),
    
    # Main pages
    path('', views.home, name='home'),
    path('orders/', views.order_list, name='order_list'),
    
    # API endpoints
    path('api/today-orders/', views.get_today_orders, name='today_orders'),
    path('api/update-order-status/', views.update_order_status, name='update_status'),
]
