from django.contrib import admin
from django.http import HttpRequest
from app.models import User, Category, Product, Supplier, DailyMetrics
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter
from django.db.models import QuerySet, Exists, OuterRef, Subquery, IntegerField
from datetime import datetime, timedelta

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User admin"""
    list_display = ('username', 'is_active', '_admin', 'is_superuser', 'date_joined', 'last_login')
    list_filter = (
        ('is_active', DropdownFilter),
        ('is_staff', DropdownFilter),
        ('is_superuser', DropdownFilter),
    )
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
    

class IsNewProductFilter(admin.SimpleListFilter):
    title = 'New Product'
    parameter_name = 'is_new_product'

    def lookups(self, request, model_admin):
        return (
            ('new', 'New'),
            ('old', 'Old'),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        old_metrics = DailyMetrics.objects.filter(
            product=OuterRef('pk'),
            date__lt=datetime.now().date() - timedelta(days=30)
        )
        queryset = queryset.annotate(
            has_old_metrics=Exists(old_metrics)
        )
        if self.value() == 'new':
            return queryset.filter(has_old_metrics=False).distinct()
        if self.value() == 'old':
            return queryset.filter(has_old_metrics=True).distinct()
        return queryset.distinct()

class InStockProductFilter(admin.SimpleListFilter):
    title = 'In Stock'
    parameter_name = 'in_stock'

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        latest_stock_subquery = DailyMetrics.objects.filter(
            product=OuterRef('pk')
        ).order_by('-date').values('stock')[:1]
        queryset = queryset.annotate(
            latest_stock_value=Subquery(latest_stock_subquery, output_field=IntegerField())
        )
        if self.value() == 'yes':
            return queryset.filter(latest_stock_value__gt=0).distinct()
        if self.value() == 'no':
            return queryset.filter(latest_stock_value__isnull=True) | queryset.filter(latest_stock_value__lte=0)
        return queryset.distinct()

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin"""
    list_display = ('code', 'name', 'category', 'supplier_list', 'has_stock_display', 'is_internet', 'is_active', 'is_new_product_display')
    search_fields = ('code', 'name')
    list_filter = (
        ('category', RelatedDropdownFilter),
        ('suppliers', RelatedDropdownFilter),
        'is_active',
        'is_internet',
        InStockProductFilter,
        IsNewProductFilter,
    )
    ordering = ['code']
    readonly_fields = ('code', 'name', 'last_purchase_price', 'currency', 'supplier_list', 'is_internet')
    fieldsets = (
        ('ERP data', {
            'fields': ('code', 'name', 'category', 'last_purchase_price', 'currency', 'supplier_list', 'is_internet')
        }),
        ('Inventory', {
            'fields': ('is_active','lead_time', 'moq')
        }),
    )
    actions = ['set_products_active', 'set_products_inactive']

    def supplier_list(self, obj):
        """Display comma-separated list of suppliers"""
        return obj.get_supplier_names() or "No suppliers"
    
    supplier_list.short_description = 'Suppliers'
    
    def is_new_product_display(self, obj: Product):
        """Show if product is new (uses model property)"""
        return obj.is_new

    def has_stock_display(self, obj: Product) -> bool:
        """True if newest daily metric stock > 0"""
        latest_metric = obj.daily_metrics.order_by('-date').first()
        return bool(latest_metric and latest_metric.stock and latest_metric.stock > 0)

    def set_products_active(self, request: HttpRequest, queryset: QuerySet):
        updated: int = queryset.update(is_active=True)
        self.message_user(request, f"{updated} products set as active.")

    def set_products_inactive(self, request: HttpRequest, queryset: QuerySet):
        updated: int = queryset.update(is_active=False)
        self.message_user(request, f"{updated} products set as inactive.")
    
    is_new_product_display.boolean = True
    is_new_product_display.short_description = 'New Product'
    has_stock_display.boolean = True
    has_stock_display.short_description = 'In Stock'
    set_products_active.short_description = "Set selected products as active"
    set_products_inactive.short_description = "Set selected products as inactive"

@admin.register(DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    """Daily metrics admin"""
    list_display = ('product', 'date', 'sales_quantity', 'stock')
    search_fields = ('product__code', 'product__name')
    list_filter = (
        ('product__category', RelatedDropdownFilter),
        ('product__suppliers', RelatedDropdownFilter),
    )
    ordering = ['-date']
    # readonly_fields = ('product', 'date', 'sales_quantity', 'stock', 'potential_sales', 'lost_sales',)
    
    def get_queryset(self, request):
        """Optimize queryset to include related product data"""
        return super().get_queryset(request).select_related('product')
