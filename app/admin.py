from django.contrib import admin
from app.models import User, Category, Product, Supplier

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User admin"""
    list_display = ('username', 'is_active', '_admin', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username',)
    ordering = ['username']
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('System Info', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def _admin(self, obj):
        """Display is_staff as Admin"""
        return obj.is_staff
    _admin.boolean = True
    _admin.short_description = 'Admin'
    
    def get_form(self, request, obj=None, change=False, **kwargs):
        """Customize field labels in the form"""
        form = super().get_form(request, obj, change=change, **kwargs)
        if 'is_staff' in form.base_fields:
            form.base_fields['is_staff'].label = 'Admin'
            form.base_fields['is_staff'].help_text = 'Allowed to access the admin interface'
        return form

@admin.register(Category)   
class CategoryAdmin(admin.ModelAdmin):
    """Product category admin"""
    list_display = ('category_code', 'name', 'parent', 'level')
    search_fields = ('category_code', 'name')
    list_filter = ('level',)
    ordering = ['level', 'category_code']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Supplier admin"""
    list_display = ('company_name', 'email', 'product_list')
    search_fields = ('company_name', 'email')
    ordering = ['company_name']
    filter_horizontal = ('products',)
    
    def product_list(self, obj):
        """Display comma-separated list of product codes for this supplier"""
        return obj.get_product_codes()
    
    product_list.short_description = 'Products'
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin"""
    list_display = ('kodas', 'pavadinimas', 'category', 'supplier_list', 'last_purchase_price')
    search_fields = ('kodas', 'pavadinimas')
    list_filter = ('category', 'suppliers')
    ordering = ['kodas']
    readonly_fields = ('last_purchase_price', 'currency', 'supplier_list')
    
    def supplier_list(self, obj):
        """Display comma-separated list of suppliers"""
        return obj.get_supplier_names() or "No suppliers"
    
    supplier_list.short_description = 'Suppliers'

