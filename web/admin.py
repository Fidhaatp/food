from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Category, Menu, WeeklyMenu, CustomFood, Order, BillReport, UserProfile

# Unregister the default User admin
admin.site.unregister(User)

# Create inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Create a new User admin
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'profile__role')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return 'No Role'
    get_role.short_description = 'Role'

# Register the new User admin
admin.site.register(User, CustomUserAdmin)

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_locked', 'created_at')
    list_filter = ('is_locked', 'created_at')
    search_fields = ('name',)
    list_editable = ('is_locked',)
    ordering = ('name',)

# Menu Admin
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_available', 'created_at')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('name', 'category__name')
    list_editable = ('is_available',)
    ordering = ('category', 'name')

# Weekly Menu Admin
@admin.register(WeeklyMenu)
class WeeklyMenuAdmin(admin.ModelAdmin):
    list_display = ('category', 'start_date', 'end_date', 'is_active')
    list_filter = ('category', 'is_active', 'start_date', 'end_date')
    search_fields = ('category__name',)
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

# Custom Food Admin
@admin.register(CustomFood)
class CustomFoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'date', 'price', 'is_available')
    list_filter = ('category', 'is_available', 'date')
    search_fields = ('name', 'category__name')
    list_editable = ('is_available',)
    date_hierarchy = 'date'
    ordering = ('-date',)

# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'date', 'price', 'status', 'created_at')
    list_filter = ('status', 'date', 'category', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'category__name')
    list_editable = ('status',)
    date_hierarchy = 'date'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'category', 'date', 'price', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Bill Report Admin
@admin.register(BillReport)
class BillReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'user_total', 'expense', 'income', 'profit', 'balance')
    list_filter = ('date',)
    search_fields = ('user__username', 'user__first_name')
    date_hierarchy = 'date'
    ordering = ('-date',)
    
    fieldsets = (
        ('Report Information', {
            'fields': ('user', 'date')
        }),
        ('Financial Data', {
            'fields': ('user_total', 'expense', 'income', 'profit', 'completed_amount', 'pending_amount', 'balance')
        }),
    )

# User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    list_editable = ('is_active',)
    ordering = ('-created_at',)

# Customize admin site
admin.site.site_header = "Food Ordering Management System"
admin.site.site_title = "Food Admin Portal"
admin.site.index_title = "Welcome to Food Admin Portal"
