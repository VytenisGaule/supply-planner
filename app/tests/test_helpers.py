from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from app.models import Product, Category, DailyMetrics
from app.helpers.utils import get_last_good_stock_date


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
        self.base_date = self.today - timedelta(days=100)
        
        # Create daily metrics with varying stock patterns
        self.create_test_metrics()
    
    def create_test_metrics(self):
        """Create test metrics with stock patterns"""
        # Days 1-30: Good stock (10-50 units)
        for i in range(30):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=5 + (i % 3),
                stock=10 + (i % 40)  # Stock ranges from 10-50
            )
        
        # Days 31-60: Declining stock (5-15 units)
        for i in range(31, 61):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=3 + (i % 2),
                stock=5 + (i % 10)  # Stock ranges from 5-15
            )
        
        # Days 61-90: Very low/zero stock (0-2 units)
        for i in range(61, 91):
            stock_level = 0 if i % 3 == 0 else (i % 3)  # Mix of 0, 1, 2
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=0 if stock_level == 0 else 1,
                stock=stock_level
            )
        
        # Days 91-100: Zero stock period
        for i in range(91, 101):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=0,
                stock=0
            )
    
    def test_get_last_good_stock_date_with_default_threshold(self):
        """Test finding last good stock date with default threshold (min_stock=1)"""
        # Should find the most recent date with stock >= 1
        last_good_date = get_last_good_stock_date(product=self.product)
        
        # Should be somewhere in the 61-90 range where stock was 1-2
        self.assertIsNotNone(last_good_date)
        self.assertGreaterEqual(last_good_date, self.base_date + timedelta(days=61))
        self.assertLess(last_good_date, self.base_date + timedelta(days=91))
    
    def test_get_last_good_stock_date_with_zero_threshold(self):
        """Test finding last good stock date with zero threshold (min_stock=0)"""
        # Should find the most recent date with stock >= 0 (which includes stock=0)
        last_good_date = get_last_good_stock_date(product=self.product, min_stock=0)
        
        # Should return the last day of our test data (day 100)
        expected_date = self.base_date + timedelta(days=100)  # Last day with any data
        self.assertEqual(last_good_date, expected_date)
    
    def test_get_last_good_stock_date_with_threshold_1(self):
        """Test finding last good stock date with threshold of 1 unit"""
        # Should find the most recent date with stock >= 1
        last_good_date = get_last_good_stock_date(
            product=self.product,
            min_stock=1
        )
        
        # Should be somewhere in the 61-90 range where stock was 1-2
        self.assertIsNotNone(last_good_date)
        self.assertGreaterEqual(last_good_date, self.base_date + timedelta(days=61))
        self.assertLess(last_good_date, self.base_date + timedelta(days=91))
    
    def test_get_last_good_stock_date_with_high_threshold(self):
        """Test finding last good stock date with high threshold (min_stock=10)"""
        # Should find the most recent date with stock >= 10
        last_good_date = get_last_good_stock_date(
            product=self.product,
            min_stock=10
        )
        
        # Should be in the first 60 days where stock was higher
        self.assertIsNotNone(last_good_date)
        self.assertGreaterEqual(last_good_date, self.base_date)
        self.assertLess(last_good_date, self.base_date + timedelta(days=61))
    
    def test_get_last_good_stock_date_with_very_high_threshold(self):
        """Test finding last good stock date with very high threshold (min_stock=100)"""
        # Should return None as we never had stock >= 100
        last_good_date = get_last_good_stock_date(
            product=self.product,
            min_stock=100
        )
        
        self.assertIsNone(last_good_date)
    
    def test_get_last_good_stock_date_no_metrics_data(self):
        """Test finding last good stock date when no metrics exist"""
        # Create a new product with no daily metrics
        new_product = Product.objects.create(
            kodas="NO_METRICS_001",
            pavadinimas="Product with No Metrics",
            category=self.category
        )
        
        last_good_date = get_last_good_stock_date(product=new_product)
        
        # Should return None as there are no metrics
        self.assertIsNone(last_good_date)
    
    def test_get_last_good_stock_date_edge_case_exact_threshold(self):
        """Test finding last good stock date when stock exactly matches threshold"""
        # Create a product with specific stock levels
        test_product = Product.objects.create(
            kodas="EDGE_TEST_001",
            pavadinimas="Edge Case Test Product",
            category=self.category
        )
        
        # Create metrics with stock exactly at threshold
        test_date = self.today - timedelta(days=5)
        DailyMetrics.objects.create(
            product=test_product,
            date=test_date,
            sales_quantity=1,
            stock=5  # Exactly 5 units
        )
        
        # Test with threshold exactly matching stock level
        last_good_date = get_last_good_stock_date(
            product=test_product,
            min_stock=5  # Exactly the stock level
        )
        
        # Should find the date since stock >= threshold
        self.assertEqual(last_good_date, test_date)
        
        # Test with threshold one higher
        last_good_date_higher = get_last_good_stock_date(
            product=test_product,
            min_stock=6  # One higher than stock level
        )
        
        # Should return None since stock < threshold
        self.assertIsNone(last_good_date_higher)
    
    def test_get_last_good_stock_date_multiple_qualifying_dates(self):
        """Test that function returns the most recent qualifying date"""
        # Create a product with multiple good stock dates
        test_product = Product.objects.create(
            kodas="MULTI_TEST_001",
            pavadinimas="Multiple Dates Test Product",
            category=self.category
        )
        
        # Create several dates with good stock (not in chronological order)
        dates_with_good_stock = []
        
        # Add older date with good stock
        older_date = self.today - timedelta(days=20)
        dates_with_good_stock.append(older_date)
        DailyMetrics.objects.create(
            product=test_product,
            date=older_date,
            sales_quantity=2,
            stock=15
        )
        
        # Add more recent date with good stock
        recent_date = self.today - timedelta(days=5)
        dates_with_good_stock.append(recent_date)
        DailyMetrics.objects.create(
            product=test_product,
            date=recent_date,
            sales_quantity=3,
            stock=12
        )
        
        # Add middle date with good stock
        middle_date = self.today - timedelta(days=10)
        dates_with_good_stock.append(middle_date)
        DailyMetrics.objects.create(
            product=test_product,
            date=middle_date,
            sales_quantity=1,
            stock=20
        )
        
        last_good_date = get_last_good_stock_date(
            product=test_product,
            min_stock=10
        )
        
        # Should return the most recent date
        expected_date = recent_date  # Most recent date
        self.assertEqual(last_good_date, expected_date)
    
    def test_get_last_good_stock_date_finds_absolute_latest(self):
        """Test that function finds the absolute latest good stock date across all history"""
        # Create a product with a long history
        test_product = Product.objects.create(
            kodas="HISTORY_TEST_001",
            pavadinimas="Long History Test Product",
            category=self.category
        )
        
        # Create very old good stock date
        very_old_date = self.today - timedelta(days=500)
        DailyMetrics.objects.create(
            product=test_product,
            date=very_old_date,
            sales_quantity=5,
            stock=50
        )
        
        # Create more recent but still old good stock date
        old_date = self.today - timedelta(days=200)
        DailyMetrics.objects.create(
            product=test_product,
            date=old_date,
            sales_quantity=3,
            stock=25
        )
        
        # Create recent zero stock dates
        for i in range(10):
            DailyMetrics.objects.create(
                product=test_product,
                date=self.today - timedelta(days=i),
                sales_quantity=0,
                stock=0
            )
        
        last_good_date = get_last_good_stock_date(
            product=test_product,
            min_stock=10
        )
        
        # Should find the more recent good stock date, not the very old one
        self.assertEqual(last_good_date, old_date)
    
    def test_get_last_good_stock_date_with_zero_stock_only(self):
        """Test finding last good stock date when all stock is zero"""
        # Create a product with only zero stock
        test_product = Product.objects.create(
            kodas="ZERO_STOCK_001",
            pavadinimas="Zero Stock Test Product",
            category=self.category
        )
        
        # Create several dates with zero stock
        for i in range(10):
            DailyMetrics.objects.create(
                product=test_product,
                date=self.today - timedelta(days=i),
                sales_quantity=0,
                stock=0
            )
        
        # With default threshold (0), return None
        last_good_date_default = get_last_good_stock_date(product=test_product)
        self.assertEqual(last_good_date_default, None)
        
        # With threshold > 0, should return None
        last_good_date_threshold = get_last_good_stock_date(
            product=test_product,
            min_stock=1
        )
        self.assertIsNone(last_good_date_threshold)
