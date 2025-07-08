from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from app.models import Product, Category, DailyMetrics
from app.helpers.utils import get_average_potential_sales


class HelpersUtilsTestCase(TestCase):
    """Test cases for helpers.utils functions"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            category_code="TEST_HELPERS",
            name="Test Helpers Category"
        )
        
        self.product = Product.objects.create(
            kodas="HELPER_TEST_001",
            pavadinimas="Test Product for Helpers",
            category=self.category,
            last_purchase_price=Decimal('25.00'),
            lead_time=30
        )
        
        # Create test date range
        self.today = date.today()
        self.base_date = self.today - timedelta(days=30)
        self.end_date = self.today
        
        # Create test metrics with various scenarios
        self.create_test_metrics()
    
    def create_test_metrics(self):
        """Create test metrics with different stock and sales patterns"""
        # Days 1-10: Good stock with various sales
        for i in range(10):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=2 + (i % 3),  # Sales: 2, 3, 4, 2, 3, 4, ...
                stock=10 + i  # Stock: 10, 11, 12, ... 19
            )
        
        # Days 11-15: Low stock (below threshold)
        for i in range(10, 15):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=1,
                stock=0  # No stock
            )
        
        # Days 16-20: Good stock again
        for i in range(15, 20):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=5,
                stock=15 + i  # Stock: 30, 31, 32, 33, 34
            )
        
        # Days 21-25: Mixed stock levels
        for i in range(20, 25):
            stock_level = 2 if i % 2 == 0 else 0
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=3 if stock_level > 0 else 0,
                stock=stock_level
            )
        
        # Days 26-30: NULL sales data (missing data)
        for i in range(25, 30):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=None,  # Missing sales data
                stock=20
            )

    def test_get_average_potential_sales_basic(self):
        """Test basic average calculation with good stock days"""
        # Calculate average from days 1-10 (good stock with min_stock=1)
        date_from = self.base_date
        date_to = self.base_date + timedelta(days=9)
        
        # Filter metrics for the date range
        metrics = self.product.daily_metrics.filter(date__range=[date_from, date_to])
        average = get_average_potential_sales(metrics, min_stock=1)
        
        # Expected: (2+3+4+2+3+4+2+3+4+2) / 10 = 29/10 = 2.9
        expected_avg = (2+3+4+2+3+4+2+3+4+2) / 10
        self.assertEqual(average, expected_avg)
    
    def test_get_average_potential_sales_high_min_stock(self):
        """Test average calculation with high min_stock threshold"""
        # Only days 16-20 have stock >= 30
        date_from = self.base_date
        date_to = self.base_date + timedelta(days=29)
        
        # Filter metrics for the date range
        metrics = self.product.daily_metrics.filter(date__range=[date_from, date_to])
        average = get_average_potential_sales(metrics, min_stock=30)
        
        # Expected: Only days 16-20 qualify (stock 30-34), all have sales=5
        self.assertEqual(average, 5.0)
    
    def test_get_average_potential_sales_no_qualifying_days(self):
        """Test average calculation when no days meet min_stock threshold"""
        date_from = self.base_date
        date_to = self.base_date + timedelta(days=29)
        
        # Filter metrics for the date range
        metrics = self.product.daily_metrics.filter(date__range=[date_from, date_to])
        average = get_average_potential_sales(metrics, min_stock=100)
        
        # Expected: 0.0 since no days have stock >= 100
        self.assertEqual(average, 0.0)
    
    def test_get_average_potential_sales_excludes_null_sales(self):
        """Test that NULL sales data is excluded from calculation"""
        # Days 26-30 have good stock but NULL sales - should be excluded
        date_from = self.base_date + timedelta(days=25)
        date_to = self.base_date + timedelta(days=29)
        
        # Filter metrics for the date range
        metrics = self.product.daily_metrics.filter(date__range=[date_from, date_to])
        average = get_average_potential_sales(metrics, min_stock=1)
        
        # Expected: 0.0 since all qualifying days have NULL sales_quantity
        self.assertEqual(average, 0.0)
    
    def test_get_average_potential_sales_mixed_stock_levels(self):
        """Test average calculation with mixed stock levels"""
        # Days 21-25: some have stock >= 2, some don't
        date_from = self.base_date + timedelta(days=20)
        date_to = self.base_date + timedelta(days=24)
        
        # Filter metrics for the date range
        metrics = self.product.daily_metrics.filter(date__range=[date_from, date_to])
        average = get_average_potential_sales(metrics, min_stock=2)
        
        # Expected: Only even days (21, 23, 25) have stock=2, all have sales=3
        self.assertEqual(average, 3.0)
    
    def test_get_average_potential_sales_empty_date_range(self):
        """Test with date range that has no metrics"""
        future_date = self.today + timedelta(days=10)
        
        # Filter metrics for the date range (should be empty)
        metrics = self.product.daily_metrics.filter(
            date__range=[future_date, future_date + timedelta(days=5)]
        )
        average = get_average_potential_sales(metrics, min_stock=1)
        
        self.assertEqual(average, 0.0)
    
    def test_get_average_potential_sales_negative_sales(self):
        """Test average calculation with negative sales (returns)"""
        # Create a product with negative sales
        test_product = Product.objects.create(
            kodas="NEG_SALES_TEST",
            pavadinimas="Negative Sales Test Product",
            category=self.category
        )
        
        test_date = self.today - timedelta(days=5)
        DailyMetrics.objects.create(
            product=test_product,
            date=test_date,
            sales_quantity=-3,  # Net returns
            stock=10
        )
        
        DailyMetrics.objects.create(
            product=test_product,
            date=test_date + timedelta(days=1),
            sales_quantity=5,  # Normal sales
            stock=12
        )
        
        # Filter metrics for the date range
        metrics = test_product.daily_metrics.filter(
            date__range=[test_date, test_date + timedelta(days=1)]
        )
        average = get_average_potential_sales(metrics, min_stock=1)
        
        # Expected: (-3 + 5) / 2 = 1.0
        self.assertEqual(average, 1.0)


class UpdateAllPotentialSalesTestCase(TestCase):
    """Test cases for Product.update_all_potential_sales method"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            category_code="UPDATE_TEST",
            name="Update Test Category"
        )
        
        self.product = Product.objects.create(
            kodas="UPDATE_TEST_001",
            pavadinimas="Update Test Product",
            category=self.category,
            last_purchase_price=Decimal('15.00'),
            lead_time=45
        )
        
        self.today = date.today()
        self.base_date = self.today - timedelta(days=20)
        
        # Create test metrics
        self.create_update_test_metrics()
    
    def create_update_test_metrics(self):
        """Create test metrics for update testing"""
        # Days 1-5: Good stock (average sales = 4.0)
        for i in range(5):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=4,
                stock=10 + i
            )
        
        # Days 6-10: No stock (should get filled with average 4.0)
        for i in range(5, 10):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=0,
                stock=0
            )
        
        # Days 11-15: Good stock again (sales = 6)
        for i in range(10, 15):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=6,
                stock=20
            )
        
        # Days 16-20: Low stock (should get filled with average)
        for i in range(15, 20):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=1,
                stock=0
            )
    
    def test_update_all_potential_sales_basic(self):
        """Test basic functionality of update_all_potential_sales"""
        # Run the update
        self.product.update_all_potential_sales(min_stock=1)
        
        # Verify results - check all metrics
        metrics = DailyMetrics.objects.filter(product=self.product).order_by('date')
        
        # Expected average from good stock days (1-5 and 11-15): (4*5 + 6*5) / 10 = 5.0
        expected_average = 5.0
        
        for i, metric in enumerate(metrics):
            if metric.stock >= 1:  # Good stock days
                # Should equal actual sales
                expected = metric.sales_quantity or 0.0
                self.assertEqual(metric.potential_sales, expected)
            else:  # Bad stock days
                # Should equal average
                self.assertEqual(metric.potential_sales, expected_average)
    
    def test_update_all_potential_sales_no_good_stock_days(self):
        """Test update when no days meet min_stock threshold"""
        # Create product with only zero stock
        test_product = Product.objects.create(
            kodas="NO_GOOD_STOCK",
            pavadinimas="No Good Stock Product",
            category=self.category
        )
        
        # Create metrics with zero stock
        for i in range(5):
            DailyMetrics.objects.create(
                product=test_product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=0,
                stock=0
            )
        
        test_product.update_all_potential_sales(min_stock=1)
        
        # All metrics should have potential_sales = 0.0
        for metric in test_product.daily_metrics.all():
            self.assertEqual(metric.potential_sales, 0.0)
    
    def test_update_all_potential_sales_with_null_sales(self):
        """Test update handling of NULL sales_quantity"""
        # Add metrics with NULL sales
        DailyMetrics.objects.create(
            product=self.product,
            date=self.base_date + timedelta(days=20),
            sales_quantity=None,  # NULL sales
            stock=15
        )
        
        DailyMetrics.objects.create(
            product=self.product,
            date=self.base_date + timedelta(days=21),
            sales_quantity=None,  # NULL sales
            stock=0  # No stock
        )
        
        self.product.update_all_potential_sales(min_stock=1)
        
        metrics = DailyMetrics.objects.filter(
            product=self.product,
            date__range=[self.base_date + timedelta(days=20), self.base_date + timedelta(days=21)]
        ).order_by('date')
        
        # First metric (good stock, NULL sales) should get 0.0
        self.assertEqual(metrics[0].potential_sales, 0.0)
        
        # Second metric (no stock) should get average from existing good stock days
        # Average from days 1-5 and 11-15: (4*5 + 6*5) / 10 = 5.0
        self.assertEqual(metrics[1].potential_sales, 5.0)
    
    def test_update_all_potential_sales_default_date_range(self):
        """Test update with default date range (oldest to today)"""
        # Should use all available metrics when no dates provided
        self.product.update_all_potential_sales()
        
        # Verify that all metrics have been updated
        all_metrics = self.product.daily_metrics.all()
        for metric in all_metrics:
            self.assertIsNotNone(metric.potential_sales)
    
    def test_update_all_potential_sales_no_metrics(self):
        """Test update when product has no metrics"""
        empty_product = Product.objects.create(
            kodas="EMPTY_PRODUCT",
            pavadinimas="Empty Product",
            category=self.category
        )
        
        # Should return early without error
        empty_product.update_all_potential_sales()
        
        # No metrics should exist
        self.assertEqual(empty_product.daily_metrics.count(), 0)
    
    def test_update_all_potential_sales_custom_min_stock(self):
        """Test update with custom min_stock threshold"""
        self.product.update_all_potential_sales(min_stock=20)  # High threshold
        
        # Only days 11-15 have stock >= 20 (all have sales=6)
        # So average should be 6.0
        expected_average = 6.0
        
        metrics = DailyMetrics.objects.filter(product=self.product).order_by('date')
        
        for metric in metrics:
            if metric.stock >= 20:  # Only days 11-15
                self.assertEqual(metric.potential_sales, 6.0)  # Actual sales
            else:  # All other days
                self.assertEqual(metric.potential_sales, expected_average)
    
    def test_update_all_potential_sales_saves_correctly(self):
        """Test that potential_sales values are actually saved to database"""
        self.product.update_all_potential_sales(min_stock=1)
        
        # Refresh from database - check first 5 days (good stock days)
        saved_metrics = DailyMetrics.objects.filter(
            product=self.product,
            date__range=[self.base_date, self.base_date + timedelta(days=4)]
        ).order_by('date')
        
        # All should have potential_sales = 4.0 (good stock days)
        for metric in saved_metrics:
            self.assertEqual(metric.potential_sales, 4.0)
