from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib.auth.models import User
from web.models import Category, Order, UserProfile, BillReport
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def register(request):
    """Manager registration page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'management/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'management/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'management/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            role='manager'
        )
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('management:login')
    
    return render(request, 'management/register.html')

def manager_login(request):
    """Manager login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'profile') and user.profile.role == 'manager':
                login(request, user)
                return redirect('management:home')
            else:
                messages.error(request, 'Access denied. This portal is for managers only.')
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'management/login.html')

@login_required
def manager_logout(request):
    """Logout manager user"""
    logout(request)
    return redirect('management:login')

@login_required
def home(request):
    """Manager home page with dashboard metrics"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('management:login')
    
    today = timezone.now().date()
    
    # Get today's statistics
    today_orders = Order.objects.filter(date=today)
    total_orders = today_orders.count()
    total_revenue = today_orders.aggregate(Sum('price'))['price__sum'] or 0
    completed_orders = today_orders.filter(status='completed').count()
    
    # Get active staff count
    active_staff = User.objects.filter(profile__role='staff', profile__is_active=True).count()
    
    # Calculate performance metrics
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0
    pending_orders = today_orders.filter(status__in=['pending', 'confirmed', 'preparing']).count()
    
    # Get total outstanding balance across all staff
    all_orders = Order.objects.all()
    total_balance = all_orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
    
    context = {
        'today': today,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'completed_orders': completed_orders,
        'active_staff': active_staff,
        'completion_rate': completion_rate,
        'avg_order_value': avg_order_value,
        'pending_orders': pending_orders,
        'total_balance': total_balance,
    }
    return render(request, 'management/home.html', context)

@login_required
def bill_report(request):
    """Bill report page with filters"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('management:login')
    
    # Get filter parameters
    filter_type = request.GET.get('filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    # Set date range based on filter
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif filter_type == 'day':
        start_date = today
        end_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    else:  # month
        start_date = today.replace(day=1)
        end_date = today
    
    # Get orders in date range
    orders = Order.objects.filter(date__range=[start_date, end_date])
    
    # Calculate summary statistics
    total_expense = orders.aggregate(Sum('price'))['price__sum'] or 0
    completed_orders = orders.filter(status='completed')
    completed_amount = completed_orders.aggregate(Sum('price'))['price__sum'] or 0
    pending_orders = orders.filter(status__in=['pending', 'confirmed', 'preparing'])
    pending_amount = pending_orders.aggregate(Sum('price'))['price__sum'] or 0
    balance = total_expense - completed_amount
    
    # Get staff summary
    staff_summary = []
    staff_users = User.objects.filter(profile__role='staff')
    
    for staff in staff_users:
        staff_orders = orders.filter(user=staff)
        staff_total = staff_orders.aggregate(Sum('price'))['price__sum'] or 0
        staff_completed = staff_orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
        staff_pending = staff_orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
        staff_balance = staff_total - staff_completed
        
        # Count unique days with orders
        unique_days = len(set(staff_orders.values_list('date', flat=True)))
        
        staff_summary.append({
            'user': staff,
            'total_days': unique_days,
            'total_amount': staff_total,
            'completed_amount': staff_completed,
            'pending_amount': staff_pending,
            'balance': staff_balance,
        })
    
    context = {
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_expense,
        'completed_revenue': completed_amount,
        'pending_revenue': pending_amount,
        'total_staff': len(staff_summary),
        'staff_summary': staff_summary,
    }
    return render(request, 'management/bill_report.html', context)

@login_required
def staff_list(request):
    """Staff list page"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('management:login')
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    staff_users = User.objects.filter(profile__role='staff').select_related('profile')
    
    # Apply search filter if provided
    if search_query:
        staff_users = staff_users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__phone_number__icontains=search_query)
        )
    
    # Get statistics for each staff member
    staff_data = []
    for staff in staff_users:
        orders = Order.objects.filter(user=staff)
        total_amount = orders.aggregate(Sum('price'))['price__sum'] or 0
        completed_amount = orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
        pending_amount = orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
        balance = total_amount - completed_amount
        
        # Count unique days with orders
        unique_days = len(set(orders.values_list('date', flat=True)))
        
        staff_data.append({
            'user': staff,
            'total_days': unique_days,
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'pending_amount': pending_amount,
            'balance': balance,
        })
    
    context = {
        'staff_data': staff_data,
        'search_query': search_query,
    }
    return render(request, 'management/staff_list.html', context)

@login_required
def member_detail(request, user_id):
    """Individual staff member detail page"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('management:login')
    
    staff_user = get_object_or_404(User, id=user_id, profile__role='staff')
    
    # Get all orders for this staff member
    orders = Order.objects.filter(user=staff_user).order_by('-date')
    
    # Calculate statistics
    total_amount = orders.aggregate(Sum('price'))['price__sum'] or 0
    completed_amount = orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
    pending_amount = orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
    balance = total_amount - completed_amount
    
    context = {
        'staff_user': staff_user,
        'orders': orders,
        'total_amount': total_amount,
        'completed_amount': completed_amount,
        'pending_amount': pending_amount,
        'balance': balance,
    }
    return render(request, 'management/member_detail.html', context)

# API Views
@login_required
def get_bill_data(request):
    """API endpoint to get bill data"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    filter_type = request.GET.get('filter', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    # Set date range
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif filter_type == 'day':
        start_date = today
        end_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    else:  # month
        start_date = today.replace(day=1)
        end_date = today
    
    orders = Order.objects.filter(date__range=[start_date, end_date])
    
    # Calculate statistics
    total_expense = orders.aggregate(Sum('price'))['price__sum'] or 0
    completed_amount = orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
    pending_amount = orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
    balance = total_expense - completed_amount
    
    return JsonResponse({
        'total_expense': float(total_expense),
        'completed_amount': float(completed_amount),
        'pending_amount': float(pending_amount),
        'balance': float(balance),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
    })

@login_required
def get_staff_data(request):
    """API endpoint to get staff data"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    staff_users = User.objects.filter(profile__role='staff')
    staff_data = []
    
    for staff in staff_users:
        orders = Order.objects.filter(user=staff)
        total_amount = orders.aggregate(Sum('price'))['price__sum'] or 0
        completed_amount = orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
        pending_amount = orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
        balance = total_amount - completed_amount
        
        # Count unique days with orders
        unique_days = len(set(orders.values_list('date', flat=True)))
        
        staff_data.append({
            'id': staff.id,
            'name': staff.first_name or staff.username,
            'email': staff.email,
            'total_days': unique_days,
            'total_amount': float(total_amount),
            'completed_amount': float(completed_amount),
            'pending_amount': float(pending_amount),
            'balance': float(balance),
        })
    
    return JsonResponse({'staff_data': staff_data})

@login_required
def update_payment(request):
    """API endpoint to update payment status"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            payment_amount = data.get('payment_amount', 0)
            payment_notes = data.get('payment_notes', '')
            mark_all_completed = data.get('mark_all_completed', False)
            
            staff_user = get_object_or_404(User, id=user_id)
            
            if mark_all_completed:
                # Mark all pending orders as completed
                orders = Order.objects.filter(user=staff_user, status__in=['pending', 'confirmed', 'preparing'])
                orders.update(status='completed')
                
                return JsonResponse({
                    'success': True, 
                    'message': f'All orders marked as completed for {staff_user.first_name or staff_user.username}'
                })
            
            else:
                # Process partial payment
                if payment_amount <= 0:
                    return JsonResponse({'error': 'Payment amount must be greater than 0'}, status=400)
                
                # Get current order totals
                total_orders = Order.objects.filter(user=staff_user)
                total_amount = total_orders.aggregate(Sum('price'))['price__sum'] or 0
                completed_amount = total_orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
                current_balance = total_amount - completed_amount
                
                if payment_amount > current_balance:
                    return JsonResponse({
                        'error': f'Payment amount (₹{payment_amount}) cannot exceed balance (₹{current_balance})'
                    }, status=400)
                
                # Update orders to completed status based on payment amount
                pending_orders = Order.objects.filter(
                    user=staff_user, 
                    status__in=['pending', 'confirmed', 'preparing']
                ).order_by('date')
                
                remaining_payment = payment_amount
                orders_to_complete = []
                
                for order in pending_orders:
                    if remaining_payment >= order.price:
                        orders_to_complete.append(order.id)
                        remaining_payment -= order.price
                    else:
                        break
                
                # Update the selected orders to completed
                if orders_to_complete:
                    Order.objects.filter(id__in=orders_to_complete).update(status='completed')
                
                # Create or update BillReport
                bill_report, created = BillReport.objects.get_or_create(
                    user=staff_user,
                    date=timezone.now().date(),
                    defaults={
                        'completed_amount': payment_amount,
                        'pending_amount': current_balance - payment_amount,
                        'balance': current_balance - payment_amount
                    }
                )
                
                if not created:
                    bill_report.completed_amount += payment_amount
                    bill_report.pending_amount = current_balance - (bill_report.completed_amount + payment_amount)
                    bill_report.balance = bill_report.pending_amount
                    bill_report.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Payment of ₹{payment_amount} processed successfully',
                    'orders_completed': len(orders_to_complete),
                    'remaining_balance': current_balance - payment_amount
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def export_staff_pdf(request):
    """Export staff list to PDF"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get staff data
    staff_users = User.objects.filter(profile__role='staff')
    staff_data = []
    
    for staff in staff_users:
        orders = Order.objects.filter(user=staff)
        total_amount = orders.aggregate(Sum('price'))['price__sum'] or 0
        completed_amount = orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
        pending_amount = orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
        balance = total_amount - completed_amount
        unique_days = len(set(orders.values_list('date', flat=True)))
        
        staff_data.append({
            'name': staff.first_name or staff.username,
            'email': staff.email,
            'phone': staff.profile.phone_number or 'Not provided',
            'status': 'Active' if staff.profile.is_active else 'Inactive',
            'total_days': unique_days,
            'total_amount': float(total_amount),
            'completed_amount': float(completed_amount),
            'pending_amount': float(pending_amount),
            'balance': float(balance),
        })
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_list_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    title = Paragraph("Staff List Report", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Add report info
    report_info = [
        ['Report Date:', timezone.now().strftime('%B %d, %Y')],
        ['Total Staff Members:', str(len(staff_data))],
        ['Generated By:', request.user.first_name or request.user.username]
    ]
    
    info_table = Table(report_info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Add staff data table
    if staff_data:
        # Prepare table data
        table_data = [['Name', 'Email', 'Phone', 'Status', 'Days', 'Total (₹)', 'Completed (₹)', 'Pending (₹)', 'Balance (₹)']]
        
        for staff in staff_data:
            table_data.append([
                staff['name'],
                staff['email'],
                staff['phone'],
                staff['status'],
                str(staff['total_days']),
                f"{staff['total_amount']:.2f}",
                f"{staff['completed_amount']:.2f}",
                f"{staff['pending_amount']:.2f}",
                f"{staff['balance']:.2f}"
            ])
        
        # Create table
        staff_table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        staff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(staff_table)
        
        # Add summary
        story.append(Spacer(1, 20))
        summary_title = Paragraph("Summary", styles['Heading2'])
        story.append(summary_title)
        story.append(Spacer(1, 10))
        
        total_staff = len(staff_data)
        active_staff = len([s for s in staff_data if s['status'] == 'Active'])
        total_amount = sum(s['total_amount'] for s in staff_data)
        total_completed = sum(s['completed_amount'] for s in staff_data)
        total_balance = sum(s['balance'] for s in staff_data)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Staff Members', str(total_staff)],
            ['Active Staff', str(active_staff)],
            ['Inactive Staff', str(total_staff - active_staff)],
            ['Total Amount (₹)', f"{total_amount:.2f}"],
            ['Total Completed (₹)', f"{total_completed:.2f}"],
            ['Total Balance (₹)', f"{total_balance:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
    else:
        no_staff = Paragraph("No staff members found.", styles['Normal'])
        story.append(no_staff)
    
    # Build PDF
    doc.build(story)
    return response

@login_required
def export_member_pdf(request, user_id):
    """Export member detail to PDF"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    staff_user = get_object_or_404(User, id=user_id)
    
    # Get member data
    orders = Order.objects.filter(user=staff_user).order_by('-date')
    total_amount = orders.aggregate(Sum('price'))['price__sum'] or 0
    completed_amount = orders.filter(status='completed').aggregate(Sum('price'))['price__sum'] or 0
    pending_amount = orders.filter(status__in=['pending', 'confirmed', 'preparing']).aggregate(Sum('price'))['price__sum'] or 0
    balance = total_amount - completed_amount
    unique_days = len(set(orders.values_list('date', flat=True)))
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="member_detail_{staff_user.username}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    title = Paragraph("Staff Member Detail Report", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Add member info
    member_info = [
        ['Name:', staff_user.first_name or staff_user.username],
        ['Email:', staff_user.email],
        ['Phone:', staff_user.profile.phone_number or 'Not provided'],
        ['Status:', 'Active' if staff_user.profile.is_active else 'Inactive'],
        ['Role:', staff_user.profile.get_role_display()],
        ['Report Date:', timezone.now().strftime('%B %d, %Y')]
    ]
    
    member_table = Table(member_info, colWidths=[2*inch, 4*inch])
    member_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(member_table)
    story.append(Spacer(1, 20))
    
    # Add statistics
    stats_title = Paragraph("Financial Summary", styles['Heading2'])
    story.append(stats_title)
    story.append(Spacer(1, 10))
    
    stats_data = [
        ['Metric', 'Amount (₹)'],
        ['Total Days with Orders', str(unique_days)],
        ['Total Amount', f"{total_amount:.2f}"],
        ['Completed Amount', f"{completed_amount:.2f}"],
        ['Pending Amount', f"{pending_amount:.2f}"],
        ['Balance', f"{balance:.2f}"]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Add order history
    if orders.exists():
        orders_title = Paragraph("Order History", styles['Heading2'])
        story.append(orders_title)
        story.append(Spacer(1, 10))
        
        # Prepare order data
        order_data = [['Date', 'Category', 'Amount (₹)', 'Status']]
        for order in orders[:20]:  # Limit to 20 orders to avoid PDF being too long
            status = 'Completed' if order.status == 'completed' else 'Pending'
            order_data.append([
                order.date.strftime('%Y-%m-%d'),
                order.category.name,
                f"{order.price:.2f}",
                status
            ])
        
        if len(orders) > 20:
            order_data.append(['...', f'... and {len(orders) - 20} more orders', '...', '...'])
        
        orders_table = Table(order_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1*inch])
        orders_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(orders_table)
    else:
        no_orders = Paragraph("No orders found for this staff member.", styles['Normal'])
        story.append(no_orders)
    
    # Build PDF
    doc.build(story)
    return response