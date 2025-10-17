from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Category, Menu, Order, UserProfile
from django.contrib.auth.models import User
from django.db.models import Q
import json

def landing_page(request):
    """Main landing page with portal selection"""
    return render(request, 'web/landing.html')

@login_required
def dashboard(request):
    """Main dashboard after login"""
    user_profile = request.user.profile
    context = {
        'user_profile': user_profile,
        'role': user_profile.role,
    }
    
    if user_profile.role == 'staff':
        return redirect('orders:home')
    elif user_profile.role == 'kitchen':
        return redirect('kitchen:home')
    elif user_profile.role == 'manager':
        return redirect('management:home')
    elif user_profile.role == 'admin':
        return redirect('admin:index')
    
    return render(request, 'web/dashboard.html', context)

def get_categories(request):
    """API endpoint to get categories for today"""
    today = timezone.now().date()
    categories = Category.objects.filter(is_locked=False)
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'price': float(category.price),
            'image': category.image.url if category.image else None,
            'is_locked': category.is_locked,
        })
    
    return JsonResponse({'categories': categories_data})

def get_menu_items(request, category_id):
    """API endpoint to get menu items for a category"""
    try:
        category = Category.objects.get(id=category_id)
        menu_items = Menu.objects.filter(category=category, is_available=True)
        
        menu_data = []
        for item in menu_items:
            menu_data.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
            })
        
        return JsonResponse({
            'category': {
                'id': category.id,
                'name': category.name,
                'price': float(category.price),
            },
            'menu_items': menu_data
        })
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
