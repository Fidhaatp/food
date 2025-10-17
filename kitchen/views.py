from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.models import User
from web.models import Category, Order, UserProfile
import json

def register(request):
    """Kitchen staff registration page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'kitchen/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'kitchen/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password
        )
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            role='kitchen'
        )
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('kitchen:login')
    
    return render(request, 'kitchen/register.html')

def kitchen_login(request):
    """Kitchen staff login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'profile') and user.profile.role == 'kitchen':
                login(request, user)
                return redirect('kitchen:home')
            else:
                messages.error(request, 'Access denied. This portal is for kitchen staff only.')
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'kitchen/login.html')

@login_required
def kitchen_logout(request):
    """Logout kitchen user"""
    logout(request)
    return redirect('kitchen:login')

@login_required
def home(request):
    """Kitchen home page - shows today's orders by category"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'kitchen':
        messages.error(request, 'Access denied.')
        return redirect('kitchen:login')
    
    today = timezone.now().date()
    
    # Get orders for today grouped by category
    today_orders = Order.objects.filter(date=today).select_related('category', 'user')
    
    # Group orders by category
    categories_with_orders = {}
    for order in today_orders:
        category = order.category
        if category.id not in categories_with_orders:
            categories_with_orders[category.id] = {
                'category': category,
                'orders': [],
                'count': 0
            }
        categories_with_orders[category.id]['orders'].append(order)
        categories_with_orders[category.id]['count'] += 1
    
    context = {
        'categories_with_orders': categories_with_orders.values(),
        'today': today,
        'total_orders': today_orders.count(),
    }
    return render(request, 'kitchen/orderlist.html', context)

@login_required
def order_list(request):
    """Detailed order list page"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'kitchen':
        messages.error(request, 'Access denied.')
        return redirect('kitchen:login')
    
    today = timezone.now().date()
    orders = Order.objects.filter(date=today).select_related('category', 'user').order_by('created_at')
    
    context = {
        'orders': orders,
        'today': today,
    }
    return render(request, 'kitchen/orderlist.html', context)

# API Views
@login_required
def get_today_orders(request):
    """API endpoint to get today's orders"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'kitchen':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.now().date()
    orders = Order.objects.filter(date=today).select_related('category', 'user')
    
    # Group by category
    categories_data = {}
    for order in orders:
        category_name = order.category.name
        if category_name not in categories_data:
            categories_data[category_name] = {
                'category': category_name,
                'count': 0,
                'orders': []
            }
        
        categories_data[category_name]['count'] += 1
        categories_data[category_name]['orders'].append({
            'id': order.id,
            'user': order.user.first_name or order.user.username,
            'created_at': order.created_at.isoformat(),
        })
    
    return JsonResponse({
        'categories': list(categories_data.values()),
        'total_orders': orders.count()
    })

@login_required
def update_order_status(request):
    """API endpoint to update order status"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'kitchen':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')
            
            valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']
            if new_status not in valid_statuses:
                return JsonResponse({'error': 'Invalid status'}, status=400)
            
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order status updated to {new_status}'
            })
            
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
