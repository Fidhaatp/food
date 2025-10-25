from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # Main landing page
    path('', views.landing, name='landing'),
]
