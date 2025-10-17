from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Main pages
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('profile/', views.profile, name='profile'),
    path('terms/', views.terms, name='terms'),
    
    # API endpoints
    path('api/categories/', views.get_categories, name='api_categories'),
    path('api/menu/<int:category_id>/', views.get_menu_items, name='api_menu'),
    path('api/place-order/', views.place_order, name='place_order'),
    path('api/user-orders/', views.get_user_orders, name='user_orders'),

    
]
