from datetime import datetime, timedelta
from typing import Union
from django.db import models
from django.db.models import QuerySet
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg


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
        return ", ".join([product.kodas for product in products])
        
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
    
    kodas = models.CharField(max_length=50, null=True, blank=True)
    pavadinimas = models.CharField(max_length=400, null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    last_purchase_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="Last purchase price")
    currency = models.CharField(max_length=10, default='USD', choices=CURRENCY_CHOICES)
    lead_time = models.PositiveIntegerField(default=120, help_text="Lead time in days including transportation and customs clearance")
    
    class Meta:
        """Meta class for Product model"""
        ordering = ['kodas']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        constraints = [
            models.UniqueConstraint(
                fields=['kodas'],
                condition=models.Q(kodas__isnull=False) & ~models.Q(kodas=''),
                name='unique_kodas_when_not_blank'
            )
        ]
        
    def __str__(self):
        return f"{self.kodas} - {self.pavadinimas}"
    
    def get_supplier_names(self):
        """Get comma-separated list of supplier names"""
        suppliers: QuerySet = self.suppliers.all()  # pylint: disable=no-member
        if not suppliers.exists():
            return "No suppliers"
        return ", ".join([supplier.company_name for supplier in suppliers])
    
    def update_all_potential_sales(self, date_from: datetime.date=None, date_to: datetime.date=None):
        """
        Calculate potential sales for all daily metrics
        """
        if not date_to:
            date_to: datetime.date = datetime.now().date()
        if not date_from:
            date_from: datetime.date = date_to - timedelta(days=365)
        metrics: QuerySet = self.daily_metrics.filter(date__range=[date_from, date_to]).order_by('date')
        for metric in metrics:
            potential: float = DailyMetrics.calculate_potential_sales_for_date(
                self, metric.date, lookback_days=30
            )
            metric.potential_sales = potential
            metric.save()
    
    def average_daily_demand(self, days_back: int = 365) -> float:
        """Calculate average daily demand from potential_sales"""
        end_date: datetime.date = datetime.now().date()
        start_date: datetime.date = end_date - timedelta(days=days_back)
        
        avg_sales = self.daily_metrics.filter(
            date__range=[start_date, end_date],
            potential_sales__isnull=False
        ).aggregate(avg=Avg('potential_sales'))['avg']
        
        return float(avg_sales) if avg_sales else 0.0

class DailyMetrics(models.Model):
    """
    Daily metrics for products with potential sales tracking
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='daily_metrics')
    date = models.DateField()
    
    # Core data
    sales_quantity = models.IntegerField(default=0, null=True, blank=True, help_text="Quantity sold - returned")
    stock = models.PositiveIntegerField(default=0, null=True, blank=True, help_text="Quantity in main warehouse")
    
    # Potential sales calculation (independent of product averages)
    potential_sales = models.FloatField(default=0, null=True, blank=True, 
                                        help_text="Potential sales based on recent sales trend when stock was adequate")
    lost_sales = models.FloatField(default=0, null=True, blank=True, 
                                   help_text="Lost sales = potential_sales - actual sales_quantity")
    is_stockout = models.BooleanField(default=False, help_text="True if stock was 0")
    
    class Meta:
        """Meta class for Daily_Metrics model"""
        unique_together = ('product', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['is_stockout']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-calculate basic metrics"""
        self.is_stockout = (self.stock == 0)
        
        # Calculate lost sales if potential_sales is provided
        if self.potential_sales is not None and self.sales_quantity is not None:
            self.lost_sales = max(0, self.potential_sales - self.sales_quantity)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def calculate_potential_sales_for_date(cls, product: Product, target_date: datetime.date, lookback_days: int=30) -> float:
        """
        Calculate potential sales for a specific date using recent adequate-stock periods
        """
        
        start_date: datetime.date = target_date - timedelta(days=lookback_days)
        try:
            target_metric = cls.objects.get(product=product, date=target_date)
        except cls.DoesNotExist:
            return 0
        
        # For good stock, potential == actual
        if not target_metric.is_stockout and target_metric.stock > 0:
            if not target_metric.sales_quantity:
                return 0
            return target_metric.sales_quantity
        
        # For stockout/low stock days, potential == average of recent "good" days
        recent_good_days: QuerySet = cls.objects.filter(
            product=product,
            date__range=[start_date, target_date - timedelta(days=1)],
            is_stockout=False,
            stock__gt=0,  # Had some stock
            sales_quantity__isnull=False
        )
        if recent_good_days.exists():
            avg_sales: Union[float, None] = recent_good_days.aggregate(avg=Avg('sales_quantity'))['avg']
            if avg_sales:
                return avg_sales
        return 0
    
    def __str__(self):
        return f"{self.product.kodas} - {self.date} (Stock: {self.stock}, Sales: {self.sales_quantity})"
