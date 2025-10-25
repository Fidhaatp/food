from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.manager_login, name='login'),
    path('logout/', views.manager_logout, name='logout'),
    
    # Main pages
    path('', views.home, name='home'),
    path('bill-report/', views.bill_report, name='bill_report'),
    path('staff-list/', views.staff_list, name='staff_list'),
    path('member-detail/<int:user_id>/', views.member_detail, name='member_detail'),
    
    # API endpoints
    path('api/bill-data/', views.get_bill_data, name='bill_data'),
    path('api/staff-data/', views.get_staff_data, name='staff_data'),
    path('api/update-payment/', views.update_payment, name='update_payment'),
    
    # Export endpoints
    path('export/staff-pdf/', views.export_staff_pdf, name='export_staff_pdf'),
    path('export/member-pdf/<int:user_id>/', views.export_member_pdf, name='export_member_pdf'),
    
    # Order management
    path('order-management/', views.order_management, name='order_management'),
    path('order-detail/', views.order_detail, name='order_detail'),
    path('api/orders-by-date/', views.get_orders_by_date, name='get_orders_by_date'),
    path('api/delete-orders/', views.delete_orders, name='delete_orders'),
    
    # Time slot management
    path('time-slot-management/', views.time_slot_management, name='time_slot_management'),
    path('api/create-time-slot/', views.create_time_slot, name='create_time_slot'),
    path('api/update-time-slot/<int:slot_id>/', views.update_time_slot, name='update_time_slot'),
    path('api/delete-time-slot/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot'),
]
