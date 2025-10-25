from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Menu(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class WeeklyMenu(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name_plural = "Weekly Menus"


class CustomFood(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        verbose_name_plural = "Custom Foods"


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.date}"

    class Meta:
        ordering = ['-created_at']


class BillReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bill_reports')
    date = models.DateField(default=timezone.now)
    user_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    completed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        ordering = ['-date']


class MenuTimeSlot(models.Model):
    """Model for managing menu availability time slots"""
    name = models.CharField(max_length=100, help_text="Name for this time slot (e.g., 'Morning Menu', 'Lunch Menu')")
    start_date = models.DateField(help_text="Start date for menu availability")
    end_date = models.DateField(help_text="End date for menu availability")
    start_time = models.TimeField(help_text="Start time for menu availability")
    end_time = models.TimeField(help_text="End time for menu availability")
    is_active = models.BooleanField(default=True, help_text="Whether this time slot is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date}) - {self.start_time} to {self.end_time}"

    class Meta:
        verbose_name = "Menu Time Slot"
        verbose_name_plural = "Menu Time Slots"
        ordering = ['-created_at']

    def is_currently_available(self):
        """Check if the current time is within the time slot"""
        from django.utils import timezone as django_timezone
        import pytz
        
        # Get current time in local timezone
        local_tz = pytz.timezone('Asia/Kolkata')
        now = django_timezone.now().astimezone(local_tz)
        current_date = now.date()
        current_time = now.time()
        
        # Check if current date is within the date range
        if not (self.start_date <= current_date <= self.end_date):
            return False
        
        # Check if current time is within the time range
        if not (self.start_time <= current_time <= self.end_time):
            return False
            
        return self.is_active

    def is_available_on_date(self, date):
        """Check if menu is available on a specific date"""
        if not (self.start_date <= date <= self.end_date):
            return False
        return self.is_active


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('kitchen', 'Kitchen'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    class Meta:
        verbose_name_plural = "User Profiles"
        
        