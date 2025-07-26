from datetime import datetime, timedelta
from typing import Optional, Union
from django.db import models
from django.db.models import QuerySet
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from app.helpers.utils import get_average_potential_sales


class User(AbstractUser):
    """
    Custom user model with simplified fields
    """
    # Remove fields we don't need by setting them to None
    first_name = None
    last_name = None
    groups = None
    user_permissions = None
    
    # Keep email field (it's useful for user management)
    # email field is inherited from AbstractUser

    class Meta:
        """ Meta class for User model"""
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        if self.username:
            return self.username
        return "N/A"


class Category(models.Model):
    """
    Hierarchical product categories (supports parent-child relationships)
    """
    category_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=400, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Hierarchical structure
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories', help_text="Parent category (null for top-level categories)")
    # Tree structure helpers
    level = models.PositiveIntegerField(default=0, help_text="Depth level in category tree (0 = root)")

    class Meta:
        """_summary_
        """
        ordering = ['level', 'category_code']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.get_path()
    
    @property
    def is_root(self) -> bool:
        """Check if this is a top-level category"""
        return self.parent is None
    
    @property
    def is_leaf(self) -> bool:
        """Check if this category has no subcategories"""
        return not getattr(self, 'subcategories').exists()
    
    def get_all_products(self) -> QuerySet:
        """Get products from this category and all its subcategories"""

        direct_products: QuerySet = self.products.all()
        subcategory_products: QuerySet = Product.objects.filter(
            category__in=self.get_descendants()
        )
        return (direct_products | subcategory_products).distinct()
    
    def get_descendants(self) -> list:
        """Get all descendant categories (recursive)"""
        descendants: list = []
        
        def collect_descendants(category):
            for subcategory in category.subcategories.all():
                descendants.append(subcategory)
                collect_descendants(subcategory)  # Recursive call
        
        collect_descendants(self)
        return descendants
    
    def get_path(self) -> str:
        """Get full category path (e.g., 'Electronics > Computers > Laptops')"""
        if self.parent is not None:
            return f"{self.parent.get_path()} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-calculate level based on parent"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)

class Supplier(models.Model):
    """
    Supplier model for products
    """
    company_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    products = models.ManyToManyField('Product', blank=True, related_name='suppliers', help_text="Products supplied by this supplier")
    
    def get_product_codes(self):
        """Get comma-separated list of products"""
        products: QuerySet = self.products.all()  # pylint: disable=no-member
        if not products.exists():
            return "No products"
        return ", ".join([product.code for product in products])
        
    def __str__(self):
        return str(self.company_name) if self.company_name is not None else ""

class Product(models.Model):
    """
    Product model from ERP
    """
    
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    ]
    
    # fields to import from ERP
    code = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=400, null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    last_purchase_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="Last purchase price")
    currency = models.CharField(max_length=10, default='USD', choices=CURRENCY_CHOICES)
    is_internet = models.BooleanField(default=False, help_text="Is e-shop")
    # fields entered or calculated
    lead_time = models.PositiveIntegerField(default=120, help_text="Lead time in days including transportation and customs clearance")
    is_active = models.BooleanField(default=False, help_text="Is active product")
    moq = models.PositiveIntegerField(default=1, help_text="Retailer MOQ if applicable")

    class Meta:
        """Meta class for Product model"""
        ordering = ['code']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=models.Q(code__isnull=False) & ~models.Q(code=''),
                name='unique_code_when_not_blank'
            )
        ]
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_supplier_names(self):
        """Get comma-separated list of supplier names"""
        suppliers: QuerySet = self.suppliers.all()
        if not suppliers.exists():
            return "No suppliers"
        return ", ".join([supplier.company_name for supplier in suppliers])
    
    def update_all_potential_sales(self, min_stock: int=1):
        """
        Calculate potential sales for all daily metrics - fill gaps with average from good stock days
        """
        
        oldest_metric : DailyMetrics = self.daily_metrics.order_by('date').first()
        newest_metric : DailyMetrics = self.daily_metrics.order_by('-date').first()
        if not oldest_metric or not newest_metric:
            return
        all_metrics: QuerySet = self.daily_metrics.filter(date__range=[oldest_metric.date, newest_metric.date])
        average_potential_sales: float = get_average_potential_sales(all_metrics, min_stock)
        for metric in all_metrics:
            if metric.stock >= min_stock:
                metric.potential_sales = metric.sales_quantity or 0.0
            else:
                metric.potential_sales = average_potential_sales
            metric.save()
    
    def get_average_daily_demand(self, days_back: int = 365) -> Optional[float]:
        """Calculate average daily demand from potential_sales"""
        end_date: datetime.date = datetime.now().date()
        start_date: datetime.date = end_date - timedelta(days=days_back - 1)
        
        avg_sales = self.daily_metrics.filter(
            date__range=[start_date, end_date],
            potential_sales__isnull=False
        ).aggregate(avg=Avg('potential_sales'))['avg']
        
        return float(avg_sales) if avg_sales is not None else None
    
    def get_remainder_days(self, days_back: int = 365) -> Optional[int]:
        """Calculate average remaining days of stock based on average daily demand"""
        avg_daily_demand: Optional[float] = self.get_average_daily_demand(days_back)
        if avg_daily_demand is None:
            return None
        if avg_daily_demand <= 0:
            return None
        latest_stock: Optional[int] = self.get_current_stock()
        if latest_stock is None:
            return None
        return int(latest_stock / avg_daily_demand)
    
    def get_current_stock(self) -> Optional[int]:
        """Get current stock level from the latest daily metrics"""
        latest_metric: DailyMetrics = self.daily_metrics.order_by('-date').first()
        if not latest_metric:
            return None
        if latest_metric.stock is None:
            return None
        return latest_metric.stock
    
    @property
    def is_new(self) -> bool:
        """Check if this product is new (no metrics 30 days ago)"""
        cutoff = datetime.now().date() - timedelta(days=30)
        return not self.daily_metrics.filter(date__lt=cutoff).exists()

class DailyMetrics(models.Model):
    """
    Daily metrics for products with potential sales tracking
    """
    # fields to import from ERP
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='daily_metrics')
    date = models.DateField()
    sales_quantity = models.IntegerField(default=0, null=True, blank=True, help_text="Quantity sold - returned")
    stock = models.PositiveIntegerField(default=0, null=True, blank=True, help_text="Quantity in main warehouse")
    # calculated fields
    potential_sales = models.FloatField(default=0, null=True, blank=True, 
                                        help_text="Potential sales based on recent sales trend when stock was adequate")
    class Meta:
        """Meta class for Daily_Metrics model"""
        unique_together = ('product', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['product', 'date']),
        ]
    
    @property
    def lost_sales(self) -> Optional[float]:
        """Calculate lost sales as potential sales minus actual sales quantity"""
        if self.potential_sales is not None and self.sales_quantity is not None:
            return max(0, self.potential_sales - self.sales_quantity)
        return None
    
    def __str__(self):
        return f"{self.product.code} - {self.date} (Stock: {self.stock}, Sales: {self.sales_quantity})"
