from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.contrib.auth.models import User
from web.models import Category, Menu, Order, UserProfile, BillReport
import json

def register(request):
    """Staff registration page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'orders/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'orders/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'orders/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            role='staff'
        )
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('orders:login')
    
    return render(request, 'orders/register.html')

def user_login(request):
    """Staff login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'profile') and user.profile.role == 'staff':
                login(request, user)
                return redirect('orders:home')
            else:
                messages.error(request, 'Access denied. This portal is for staff only.')
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'orders/login.html')

@login_required
def user_logout(request):
    """Logout user"""
    logout(request)
    return redirect('orders:login')

@login_required
def home(request):
    """Staff home page - shows today's categories"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'staff':
        messages.error(request, 'Access denied.')
        return redirect('orders:login')
    
    today = timezone.now().date()
    
    # Get available categories (not locked and have menu items)
    categories = Category.objects.filter(
        is_locked=False
    ).prefetch_related('menus').filter(
        menus__is_available=True
    ).distinct()
    
    # Get user's orders for today
    today_orders = Order.objects.filter(user=request.user, date=today)
    ordered_categories = [order.category.id for order in today_orders]
    
    context = {
        'categories': categories,
        'today_orders': today_orders,
        'ordered_categories': ordered_categories,
        'today': today,
    }
    return render(request, 'orders/index.html', context)

@login_required
def menu(request):
    """Menu page with category selection"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'staff':
        messages.error(request, 'Access denied.')
        return redirect('orders:login')
    
    # Get available categories (not locked and have menu items)
    categories = Category.objects.filter(
        is_locked=False
    ).prefetch_related('menus').filter(
        menus__is_available=True
    ).distinct()
    
    today = timezone.now().date()
    
    # Get user's orders for today
    today_orders = Order.objects.filter(user=request.user, date=today)
    
    context = {
        'categories': categories,
        'today_orders': today_orders,
        'today': today,
    }
    return render(request, 'orders/menu.html', context)

@login_required
def profile(request):
    """User profile page with order history and statistics"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'staff':
        messages.error(request, 'Access denied.')
        return redirect('orders:login')
    
    user = request.user
    today = timezone.now().date()
    
    # Get filter parameters
    filter_type = request.GET.get('filter', 'month')
    
    if filter_type == 'day':
        start_date = today
        end_date = today
    elif filter_type == 'week':
        start_date = today - timezone.timedelta(days=7)
        end_date = today
    else:  # month
        start_date = today.replace(day=1)
        end_date = today
    
    # Get orders in date range
    orders = Order.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    )
    
    # Calculate statistics
    total_amount = orders.aggregate(Sum('price'))['price__sum'] or 0
    completed_orders = orders.filter(status='completed')
    completed_amount = completed_orders.aggregate(Sum('price'))['price__sum'] or 0
    pending_orders = orders.filter(status__in=['pending', 'confirmed', 'preparing'])
    pending_amount = pending_orders.aggregate(Sum('price'))['price__sum'] or 0
    balance = total_amount - completed_amount
    
    context = {
        'user': user,
        'orders': orders,
        'total_amount': total_amount,
        'completed_amount': completed_amount,
        'pending_amount': pending_amount,
        'balance': balance,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'orders/profile.html', context)

def terms(request):
    """Terms and conditions page"""
    return render(request, 'orders/terms.html')

# API Views
@login_required
def get_categories(request):
    """API endpoint to get categories"""
    # Get available categories (not locked and have menu items)
    categories = Category.objects.filter(
        is_locked=False
    ).prefetch_related('menus').filter(
        menus__is_available=True
    ).distinct()
    
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

@login_required
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

@login_required
def place_order(request):
    """API endpoint to place an order"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')
            
            category = Category.objects.get(id=category_id)
            
            # Check if user already ordered this category today
            today = timezone.now().date()
            existing_order = Order.objects.filter(
                user=request.user,
                category=category,
                date=today
            ).first()
            
            if existing_order:
                return JsonResponse({'error': 'You have already ordered this category today'}, status=400)
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                category=category,
                date=today,
                price=category.price,
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'message': 'Order placed successfully!'
            })
            
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def get_user_orders(request):
    """API endpoint to get user's orders"""
    today = timezone.now().date()
    orders = Order.objects.filter(user=request.user, date=today)
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'category': order.category.name,
            'price': float(order.price),
            'status': order.status,
            'created_at': order.created_at.isoformat(),
        })
    
    return JsonResponse({'orders': orders_data})
