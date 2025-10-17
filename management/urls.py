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
]
