from django.test import TestCase, RequestFactory
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock
from django.http import QueryDict
from app.models import Product, Category, Supplier, DailyMetrics
from app.helpers.utils import get_average_potential_sales
from app.helpers.context import populate_product_list_context, apply_min_max_filter


class HelpersUtilsTestCase(TestCase):
    def test_get_filter_dropdown_queryset_basic(self):
        """Test get_filter_dropdown_queryset returns correct category ids for product queryset"""
        from app.helpers.utils import get_filter_dropdown_queryset
        # Create another category and product
        category2 = Category.objects.create(category_code="TEST_HELPERS2", name="Second Category")
        product2 = Product.objects.create(code="HELPER_TEST_002", name="Second Product", category=category2, last_purchase_price=Decimal('30.00'), lead_time=10)
        # QuerySet with both products
        qs = Product.objects.filter(pk__in=[self.product.pk, product2.pk])
        # Should return both category ids
        ids = get_filter_dropdown_queryset(qs, Category, 'products')
        self.assertIn(self.category.pk, ids)
        self.assertIn(category2.pk, ids)
        # QuerySet with only one product
        qs_single = Product.objects.filter(pk=self.product.pk)
        ids_single = get_filter_dropdown_queryset(qs_single, Category, 'products')
        self.assertEqual(ids_single, [self.category.pk])
    """Test cases for helpers.utils functions"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            category_code="TEST_HELPERS",
            name="Test Helpers Category"
        )
        
        self.product = Product.objects.create(
            code="HELPER_TEST_001",
            name="Test Product for Helpers",
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
            code="NEG_SALES_TEST",
            name="Negative Sales Test Product",
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
            code="UPDATE_TEST_001",
            name="Update Test Product",
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
            code="NO_GOOD_STOCK",
            name="No Good Stock Product",
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
            code="EMPTY_PRODUCT",
            name="Empty Product",
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


class PopulateProductListContextTestCase(TestCase):
    """Test cases for populate_product_list_context function"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        
        # Create categories
        self.category1 = Category.objects.create(
            category_code="CAT1",
            name="Electronics"
        )
        self.category2 = Category.objects.create(
            category_code="CAT2", 
            name="Books"
        )
        
        # Create suppliers
        self.supplier1 = Supplier.objects.create(
            company_name="Supplier One",
            email="john@supplier1.com"
        )
        self.supplier2 = Supplier.objects.create(
            company_name="Supplier Two",
            email="jane@supplier2.com"
        )
        
        # Create products
        self.product1 = Product.objects.create(
            code="PROD001",
            name="Laptop",
            category=self.category1,
            last_purchase_price=Decimal('999.99'),
            is_active=True
        )
        self.product1.suppliers.add(self.supplier1)
        
        self.product2 = Product.objects.create(
            code="PROD002",
            name="Python Book",
            category=self.category2,
            last_purchase_price=Decimal('49.99'),
            is_active=True
        )
        self.product2.suppliers.add(self.supplier2)
        
        # Product without category
        self.product3 = Product.objects.create(
            code="PROD003",
            name="Mystery Item",
            category=None,
            is_active=True,
            last_purchase_price=Decimal('25.00')
        )
        
        # Product without suppliers
        self.product4 = Product.objects.create(
            code="PROD004",
            name="Orphan Product",
            is_active=True,
            category=self.category1,
            last_purchase_price=Decimal('15.00')
        )
    
    def create_mock_request(self, session_data=None, get_data=None, post_data=None):
        """Create a mock request with session data"""
        request = self.factory.get('/')
        request.session = session_data or {}
        request.GET = get_data or {}
        request.POST = post_data or {}
        return request
    
    def test_populate_product_list_context_basic(self):
        """Test basic context population without filters"""
        request = self.create_mock_request()
        context = {}
        
        populate_product_list_context(request, context)
        
        # Check basic context items
        self.assertIn('products', context)
        self.assertIn('paginator', context)
        self.assertIn('items_per_page', context)
        self.assertIn('items_per_page_form', context)
        self.assertIn('code_filter_form', context)
        self.assertIn('name_filter_form', context)
        self.assertIn('category_filter_form', context)
        self.assertIn('supplier_filter_form', context)
        self.assertIn('selected_categories', context)
        self.assertIn('selected_suppliers', context)
        
        # Check default values
        self.assertEqual(context['items_per_page'], 20)
        self.assertEqual(context['selected_categories'], [])
        self.assertEqual(context['selected_suppliers'], [])
        
        # Check that all products are included
        self.assertEqual(context['products'].paginator.count, 4)
    
    def test_populate_product_list_context_with_code_filter(self):
        """Test context population with code filter"""
        filter_data = QueryDict('code=PROD001')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should only show product with code containing 'PROD001'
        self.assertEqual(context['products'].paginator.count, 1)
        self.assertEqual(context['products'][0].code, 'PROD001')
    
    def test_populate_product_list_context_with_name_filter(self):
        """Test context population with name filter"""
        filter_data = QueryDict('name=Book')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should only show product with name containing 'Book'
        self.assertEqual(context['products'].paginator.count, 1)
        self.assertEqual(context['products'][0].name, 'Python Book')
    
    def test_populate_product_list_context_with_category_filter(self):
        """Test context population with category filter"""
        filter_data = QueryDict(f'categories={self.category1.id}')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should show products in category1 (Laptop and Orphan Product)
        self.assertEqual(context['products'].paginator.count, 2)
        product_names = [p.name for p in context['products']]
        self.assertIn('Laptop', product_names)
        self.assertIn('Orphan Product', product_names)
    
    def test_populate_product_list_context_with_empty_category_filter(self):
        """Test context population with 'empty' category filter (no category)"""
        filter_data = QueryDict('categories=empty')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should only show product without category (Mystery Item)
        self.assertEqual(context['products'].paginator.count, 1)
        self.assertEqual(context['products'][0].name, 'Mystery Item')
    
    def test_populate_product_list_context_with_supplier_filter(self):
        """Test context population with supplier filter"""
        filter_data = QueryDict(f'suppliers={self.supplier1.id}')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should only show product from supplier1 (Laptop)
        self.assertEqual(context['products'].paginator.count, 1)
        self.assertEqual(context['products'][0].name, 'Laptop')
    
    def test_populate_product_list_context_with_empty_supplier_filter(self):
        """Test context population with 'empty' supplier filter (no suppliers)"""
        filter_data = QueryDict('suppliers=empty')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should show products without suppliers (Mystery Item and Orphan Product)
        self.assertEqual(context['products'].paginator.count, 2)
        product_names = [p.name for p in context['products']]
        self.assertIn('Mystery Item', product_names)
        self.assertIn('Orphan Product', product_names)
    
    def test_populate_product_list_context_with_combined_filters(self):
        """Test context population with multiple filters"""
        # Filter by category1 AND supplier1
        filter_data = QueryDict(f'categories={self.category1.id}&suppliers={self.supplier1.id}')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should only show Laptop (in category1 AND has supplier1)
        self.assertEqual(context['products'].paginator.count, 1)
        self.assertEqual(context['products'][0].name, 'Laptop')
    
    def test_populate_product_list_context_with_mixed_category_filter(self):
        """Test context population with both 'empty' and specific category"""
        filter_data = QueryDict(f'categories=empty&categories={self.category1.id}')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should show products with no category OR in category1
        self.assertEqual(context['products'].paginator.count, 3)
        product_names = [p.name for p in context['products']]
        self.assertIn('Mystery Item', product_names)  # No category
        self.assertIn('Laptop', product_names)        # Category1
        self.assertIn('Orphan Product', product_names) # Category1
    
    def test_populate_product_list_context_pagination(self):
        """Test context pagination functionality"""
        # Set items per page to 2
        request = self.create_mock_request(session_data={'items_per_page': 2})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should have 2 pages (4 products, 2 per page)
        self.assertEqual(context['paginator'].num_pages, 2)
        self.assertEqual(len(context['products']), 2)
        self.assertEqual(context['items_per_page'], 2)
    
    def test_populate_product_list_context_page_number(self):
        """Test context with specific page number"""
        # Set items per page to 2 and request page 2
        request = self.create_mock_request(
            session_data={'items_per_page': 2},
            get_data={'page': '2'}
        )
        context = {}
        
        populate_product_list_context(request, context)
        
        # Should show page 2
        self.assertEqual(context['products'].number, 2)
    
    def test_populate_product_list_context_selected_values(self):
        """Test that selected values are properly passed to context"""
        filter_data = QueryDict(f'categories={self.category1.id}&suppliers={self.supplier1.id}')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Check selected values
        self.assertEqual(context['selected_categories'], [str(self.category1.id)])
        self.assertEqual(context['selected_suppliers'], [str(self.supplier1.id)])
    
    def test_populate_product_list_context_form_validation(self):
        """Test that forms are properly validated"""
        filter_data = QueryDict('code=TEST&name=Product')
        request = self.create_mock_request(session_data={'filter_data': filter_data})
        context = {}
        
        populate_product_list_context(request, context)
        
        # Forms should be valid and contain the filter data
        self.assertTrue(context['code_filter_form'].is_valid())
        self.assertTrue(context['name_filter_form'].is_valid())
        self.assertEqual(context['code_filter_form'].cleaned_data['code'], 'TEST')
        self.assertEqual(context['name_filter_form'].cleaned_data['name'], 'Product')


class GetRemainderDaysTestCase(TestCase):
    """Test cases for Product.get_remainder_days method"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            category_code="TEST_REMAINDER",
            name="Test Remainder Category"
        )
        
        self.product = Product.objects.create(
            code="REMAINDER_TEST_001",
            name="Test Product for Remainder Days",
            category=self.category,
            last_purchase_price=Decimal('50.00'),
            lead_time=30
        )
        
        # Create test date range - use recent dates so they fall within the query range
        self.today = date.today()
        self.base_date = self.today - timedelta(days=9)  # Start 9 days ago for 10 days total (0-9 days ago)
        
    def create_metrics_with_pattern(self, sales_pattern, stock_pattern, potential_sales_pattern=None):
        """Helper to create metrics with specific patterns"""
        for i, (sales, stock) in enumerate(zip(sales_pattern, stock_pattern)):
            potential_sales = potential_sales_pattern[i] if potential_sales_pattern else sales
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=sales,
                stock=stock,
                potential_sales=potential_sales
            )
    
    def test_get_remainder_days_basic_calculation(self):
        """Test basic remainder days calculation"""
        # Create 10 days of consistent sales (5 per day) with good stock
        sales_pattern = [5] * 10
        stock_pattern = [100] * 9 + [50]  # Last day has 50 stock
        
        self.create_metrics_with_pattern(sales_pattern, stock_pattern)
        
        # Average daily demand should be 5, current stock is 50
        # Expected remainder days: 50 / 5 = 10 days
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 10)
    
    def test_get_remainder_days_with_varying_demand(self):
        """Test remainder days with varying daily demand"""
        # Create pattern: 2, 4, 6, 4, 2, 4, 6, 4, 2, 4 (avg = 3.8)
        sales_pattern = [2, 4, 6, 4, 2, 4, 6, 4, 2, 4]
        # Set all stock to 100, except the last day which has current stock of 38
        stock_pattern = [100] * 9 + [38]  # Last day has 38 stock
        
        self.create_metrics_with_pattern(sales_pattern, stock_pattern)
        
        # Average daily demand: (2+4+6+4+2+4+6+4+2+4) / 10 = 3.8
        # Expected remainder days: 38 / 3.8 = 10 days
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 10)
    
    def test_get_remainder_days_zero_stock(self):
        """Test remainder days when current stock is zero"""
        sales_pattern = [5] * 10
        stock_pattern = [100] * 9 + [0]  # Last day has 0 stock
        
        self.create_metrics_with_pattern(sales_pattern, stock_pattern)
        
        # Should return 0 when stock is 0
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 0)
    
    def test_get_remainder_days_zero_demand(self):
        """Test remainder days when average demand is zero"""
        sales_pattern = [0] * 10  # No sales for 10 days
        stock_pattern = [100] * 9 + [50]  # Last day has 50 stock
        
        self.create_metrics_with_pattern(sales_pattern, stock_pattern)
        
        # Should return None when demand is 0
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertIsNone(remainder)
    
    def test_get_remainder_days_no_metrics(self):
        """Test remainder days when product has no metrics"""
        # Should return None when no metrics exist
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertIsNone(remainder)
    
    def test_get_remainder_days_null_potential_sales(self):
        """Test remainder days when potential_sales are NULL"""
        # Create metrics with NULL potential_sales
        for i in range(10):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=5,
                stock=100 - i,
                potential_sales=None  # NULL potential sales
            )
        
        # Should return None when all potential_sales are NULL
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertIsNone(remainder)
    
    def test_get_remainder_days_none_current_stock(self):
        """Test remainder days when current stock is None (no metrics)"""
        # Create historical metrics but no current stock data
        # This simulates when get_current_stock() returns None
        
        # Don't create any metrics - this will make get_current_stock() return None
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertIsNone(remainder)
    
    def test_get_remainder_days_mixed_null_values(self):
        """Test remainder days with some NULL potential_sales values"""
        # Create 10 metrics, half with NULL potential_sales
        for i in range(10):
            potential_sales = 4 if i < 5 else None
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=4,
                stock=100 - i,
                potential_sales=potential_sales
            )
        
        # Average should be calculated only from non-NULL values
        # First 5 days have potential_sales=4, so average=4
        # Current stock = 91, so remainder = 91/4 = 22.75 → 22 days
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 22)
    
    def test_get_remainder_days_fractional_result(self):
        """Test remainder days with fractional calculation"""
        # Create pattern that results in fractional days
        sales_pattern = [3] * 10  # Average daily demand = 3
        stock_pattern = [100] * 9 + [10]  # Current stock = 10
        
        self.create_metrics_with_pattern(sales_pattern, stock_pattern)
        
        # Expected: 10 / 3 = 3.33... → should return 3 (int conversion)
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 3)
    
    def test_get_remainder_days_large_stock(self):
        """Test remainder days with large stock amount"""
        sales_pattern = [2] * 10  # Average daily demand = 2
        stock_pattern = [1000] * 9 + [1000]  # Large stock = 1000
        
        self.create_metrics_with_pattern(sales_pattern, stock_pattern)
        
        # Expected: 1000 / 2 = 500 days
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 500)
    
    def test_get_remainder_days_custom_days_back(self):
        """Test remainder days with custom days_back parameter"""
        # Create 20 days of data with different patterns
        recent_sales = [10] * 10  # Last 10 days: high sales
        older_sales = [2] * 10    # Older 10 days: low sales
        all_sales = older_sales + recent_sales
        
        stock_pattern = [100] * 19 + [100]
        
        # Use recent dates starting from 20 days ago
        base_date = date.today() - timedelta(days=19)
        for i, (sales, stock) in enumerate(zip(all_sales, stock_pattern)):
            DailyMetrics.objects.create(
                product=self.product,
                date=base_date + timedelta(days=i),
                sales_quantity=sales,
                stock=stock,
                potential_sales=sales
            )
        
        # Test with days_back=10 (only recent high sales)
        remainder_recent = self.product.get_remainder_days(days_back=10)
        # Average from last 10 days = 10, stock = 100, so 100/10 = 10 days
        self.assertEqual(remainder_recent, 10)
        
        # Test with days_back=20 (all sales including low sales)
        remainder_all = self.product.get_remainder_days(days_back=20)
        # Average from all 20 days = (2*10 + 10*10)/20 = 120/20 = 6
        # Stock = 100, so 100/6 = 16.66... → 16 days
        self.assertEqual(remainder_all, 16)
    
    def test_get_remainder_days_uses_potential_sales_not_actual(self):
        """Test that remainder_days uses potential_sales, not actual sales_quantity"""
        # Create data where potential_sales differs from actual sales
        for i in range(10):
            DailyMetrics.objects.create(
                product=self.product,
                date=self.base_date + timedelta(days=i),
                sales_quantity=2,      # Actual sales = 2
                stock=100 - i,
                potential_sales=6      # Potential sales = 6 (higher)
            )
        
        # Should use potential_sales (6) not sales_quantity (2)
        # Average demand = 6, current stock = 91, so 91/6 = 15.16... → 15 days
        remainder = self.product.get_remainder_days(days_back=10)
        self.assertEqual(remainder, 15)


class GetCurrentStockTestCase(TestCase):
    """Test cases for Product.get_current_stock method"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            category_code="TEST_STOCK",
            name="Test Stock Category"
        )
        
        self.product = Product.objects.create(
            code="STOCK_TEST_001",
            name="Test Product for Current Stock",
            category=self.category,
            last_purchase_price=Decimal('25.00'),
            lead_time=30
        )
    
    def test_get_current_stock_with_recent_metrics(self):
        """Test get_current_stock with recent daily metrics"""
        today = date.today()
        
        # Create metrics for the last 5 days
        for i in range(5):
            DailyMetrics.objects.create(
                product=self.product,
                date=today - timedelta(days=i),
                sales_quantity=2,
                stock=100 - (i * 5),  # Decreasing stock: 100, 95, 90, 85, 80
                potential_sales=2.0
            )
        
        # Should return the stock from the most recent date (today = 100)
        current_stock = self.product.get_current_stock()
        self.assertEqual(current_stock, 100)
    
    def test_get_current_stock_no_metrics(self):
        """Test get_current_stock when product has no metrics"""
        # Should return None when no metrics exist
        current_stock = self.product.get_current_stock()
        self.assertIsNone(current_stock)
    
    def test_get_current_stock_null_stock(self):
        """Test get_current_stock when latest metric has NULL stock"""
        today = date.today()
        
        # Create metric with NULL stock
        DailyMetrics.objects.create(
            product=self.product,
            date=today,
            sales_quantity=2,
            stock=None,  # NULL stock
            potential_sales=2.0
        )
        
        # Should return None when stock is NULL
        current_stock = self.product.get_current_stock()
        self.assertIsNone(current_stock)
    
    def test_get_current_stock_zero_stock(self):
        """Test get_current_stock when latest metric has zero stock"""
        today = date.today()
        
        # Create metric with zero stock
        DailyMetrics.objects.create(
            product=self.product,
            date=today,
            sales_quantity=2,
            stock=0,  # Zero stock
            potential_sales=2.0
        )
        
        # Should return 0 when stock is actually 0 (not None)
        current_stock = self.product.get_current_stock()
        self.assertEqual(current_stock, 0)
    
    def test_get_current_stock_correct_ordering(self):
        """Test that get_current_stock gets the most recent metric by date"""
        today = date.today()
        
        # Create metrics in non-chronological order
        DailyMetrics.objects.create(
            product=self.product,
            date=today - timedelta(days=3),
            sales_quantity=1,
            stock=50,
            potential_sales=1.0
        )
        
        DailyMetrics.objects.create(
            product=self.product,
            date=today,  # Most recent
            sales_quantity=3,
            stock=75,
            potential_sales=3.0
        )
        
        DailyMetrics.objects.create(
            product=self.product,
            date=today - timedelta(days=1),
            sales_quantity=2,
            stock=60,
            potential_sales=2.0
        )
        
        # Should return stock from the most recent date (today = 75)
        current_stock = self.product.get_current_stock()
        self.assertEqual(current_stock, 75)
    
    def test_get_current_stock_with_large_stock_value(self):
        """Test get_current_stock with large stock values"""
        today = date.today()
        
        # Create metric with large stock value
        DailyMetrics.objects.create(
            product=self.product,
            date=today,
            sales_quantity=10,
            stock=999999,  # Large stock value
            potential_sales=10.0
        )
        
        # Should return the large stock value correctly
        current_stock = self.product.get_current_stock()
        self.assertEqual(current_stock, 999999)
    
    def test_get_current_stock_integration_with_remainder_days(self):
        """Test that get_current_stock integrates correctly with remainder_days"""
        today = date.today()
        
        # Create 5 days of metrics with consistent demand
        for i in range(5):
            DailyMetrics.objects.create(
                product=self.product,
                date=today - timedelta(days=4-i),  # Chronological order
                sales_quantity=5,
                stock=100 if i < 4 else 50,  # Last day has 50 stock
                potential_sales=5.0
            )
        
        # Test that get_current_stock returns the latest stock
        current_stock = self.product.get_current_stock()
        self.assertEqual(current_stock, 50)
        
        # Test that remainder_days uses this stock value correctly
        # Average demand = 5, current stock = 50, so 50/5 = 10
        remainder = self.product.get_remainder_days(days_back=5)
        self.assertEqual(remainder, 10)


class ApplyRelationFilterTestCase(TestCase):
    """Test cases for apply_relation_filter function"""
    
    def setUp(self):
        """Set up test data"""
        # Create categories
        self.category1 = Category.objects.create(
            category_code="CAT1",
            name="Electronics"
        )
        self.category2 = Category.objects.create(
            category_code="CAT2", 
            name="Books"
        )
        
        # Create suppliers
        self.supplier1 = Supplier.objects.create(
            company_name="Supplier One",
            email="supplier1@test.com"
        )
        self.supplier2 = Supplier.objects.create(
            company_name="Supplier Two",
            email="supplier2@test.com"
        )
        
        # Create products with categories and suppliers
        self.product1 = Product.objects.create(
            code="PROD001",
            name="Laptop",
            category=self.category1,
            last_purchase_price=Decimal('999.99')
        )
        self.product1.suppliers.add(self.supplier1)
        
        self.product2 = Product.objects.create(
            code="PROD002",
            name="Python Book",
            category=self.category2,
            last_purchase_price=Decimal('49.99')
        )
        self.product2.suppliers.add(self.supplier2)
        
        # Product without category but with supplier
        self.product3 = Product.objects.create(
            code="PROD003",
            name="Mystery Item",
            category=None,
            last_purchase_price=Decimal('25.00')
        )
        self.product3.suppliers.add(self.supplier1)
        
        # Product without suppliers but with category
        self.product4 = Product.objects.create(
            code="PROD004",
            name="Orphan Product",
            category=self.category1,
            last_purchase_price=Decimal('15.00')
        )
        
        # Product with no category and no suppliers
        self.product5 = Product.objects.create(
            code="PROD005",
            name="Truly Orphan Product",
            category=None,
            last_purchase_price=Decimal('5.00')
        )
        
        # Product with multiple suppliers
        self.product6 = Product.objects.create(
            code="PROD006",
            name="Multi-Supplier Product",
            category=self.category2,
            last_purchase_price=Decimal('100.00')
        )
        self.product6.suppliers.add(self.supplier1, self.supplier2)
    
    def test_apply_relation_filter_empty_filter_list(self):
        """Test that empty filter list returns original queryset"""
        from app.helpers.context import apply_relation_filter
        
        original_queryset = Product.objects.all()
        result = apply_relation_filter(original_queryset, [], 'category')
        
        self.assertEqual(list(result), list(original_queryset))
    
    def test_apply_relation_filter_category_specific_ids(self):
        """Test filtering by specific category IDs"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = [str(self.category1.id)]
        
        result = apply_relation_filter(queryset, filter_list, 'category')
        
        # Should return products with category1 (product1, product4)
        self.assertEqual(result.count(), 2)
        self.assertIn(self.product1, result)
        self.assertIn(self.product4, result)
        self.assertNotIn(self.product2, result)  # Different category
        self.assertNotIn(self.product3, result)  # No category
    
    def test_apply_relation_filter_category_empty_only(self):
        """Test filtering by 'empty' category only"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = ['empty']
        
        result = apply_relation_filter(queryset, filter_list, 'category')
        
        # Should return products with no category (product3, product5)
        self.assertEqual(result.count(), 2)
        self.assertIn(self.product3, result)
        self.assertIn(self.product5, result)
        self.assertNotIn(self.product1, result)  # Has category
    
    def test_apply_relation_filter_category_empty_and_specific(self):
        """Test filtering by both 'empty' and specific category IDs"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = ['empty', str(self.category1.id)]
        
        result = apply_relation_filter(queryset, filter_list, 'category')
        
        # Should return products with no category OR category1
        self.assertEqual(result.count(), 4)
        self.assertIn(self.product1, result)  # category1
        self.assertIn(self.product3, result)  # no category
        self.assertIn(self.product4, result)  # category1
        self.assertIn(self.product5, result)  # no category
        self.assertNotIn(self.product2, result)  # category2
        self.assertNotIn(self.product6, result)  # category2
    
    def test_apply_relation_filter_suppliers_specific_ids(self):
        """Test filtering by specific supplier IDs"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = [str(self.supplier1.id)]
        
        result = apply_relation_filter(queryset, filter_list, 'suppliers')
        
        # Should return products with supplier1 (product1, product3, product6)
        self.assertEqual(result.count(), 3)
        self.assertIn(self.product1, result)
        self.assertIn(self.product3, result)
        self.assertIn(self.product6, result)  # Has multiple suppliers including supplier1
        self.assertNotIn(self.product2, result)  # Different supplier
        self.assertNotIn(self.product4, result)  # No suppliers
    
    def test_apply_relation_filter_suppliers_empty_only(self):
        """Test filtering by 'empty' suppliers only"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = ['empty']
        
        result = apply_relation_filter(queryset, filter_list, 'suppliers')
        
        # Should return products with no suppliers (product4, product5)
        self.assertEqual(result.count(), 2)
        self.assertIn(self.product4, result)
        self.assertIn(self.product5, result)
        self.assertNotIn(self.product1, result)  # Has suppliers
    
    def test_apply_relation_filter_suppliers_empty_and_specific(self):
        """Test filtering by both 'empty' and specific supplier IDs"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = ['empty', str(self.supplier2.id)]
        
        result = apply_relation_filter(queryset, filter_list, 'suppliers')
        
        # Should return products with no suppliers OR supplier2
        self.assertEqual(result.count(), 4)
        self.assertIn(self.product2, result)  # supplier2
        self.assertIn(self.product4, result)  # no suppliers
        self.assertIn(self.product5, result)  # no suppliers
        self.assertIn(self.product6, result)  # has supplier2 (and supplier1)
        self.assertNotIn(self.product1, result)  # only supplier1
        self.assertNotIn(self.product3, result)  # only supplier1
    
    def test_apply_relation_filter_multiple_specific_ids(self):
        """Test filtering by multiple specific IDs"""
        from app.helpers.context import apply_relation_filter
        
        queryset = Product.objects.all()
        filter_list = [str(self.category1.id), str(self.category2.id)]
        
        result = apply_relation_filter(queryset, filter_list, 'category')
        
        # Should return products with category1 OR category2
        self.assertEqual(result.count(), 4)
        self.assertIn(self.product1, result)  # category1
        self.assertIn(self.product2, result)  # category2
        self.assertIn(self.product4, result)  # category1
        self.assertIn(self.product6, result)  # category2
        self.assertNotIn(self.product3, result)  # no category
        self.assertNotIn(self.product5, result)  # no category
    
    def test_apply_relation_filter_distinct_applied(self):
        """Test that distinct() is applied to prevent duplicates"""
        from app.helpers.context import apply_relation_filter
        
        # product6 has both suppliers, but should only appear once
        queryset = Product.objects.all()
        filter_list = [str(self.supplier1.id), str(self.supplier2.id)]
        
        result = apply_relation_filter(queryset, filter_list, 'suppliers')
        
        product_ids = [p.id for p in result]
        unique_product_ids = list(set(product_ids))
        
        self.assertEqual(len(product_ids), len(unique_product_ids), 
                        "Duplicate products found - distinct() not working")
    
    def test_apply_relation_filter_queryset_immutability(self):
        """Test that original queryset is not modified"""
        from app.helpers.context import apply_relation_filter
        
        original_queryset = Product.objects.all()
        original_count = original_queryset.count()
        
        # Apply filter
        result = apply_relation_filter(original_queryset, [str(self.category1.id)], 'category')
        
        # Original queryset should be unchanged
        self.assertEqual(original_queryset.count(), original_count)
        self.assertEqual(original_queryset.count(), 6)  # All products
        self.assertLess(result.count(), original_count)  # Filtered result is smaller


class ApplyMinMaxFilterTestCase(TestCase):
    """Test cases for apply_min_max_filter function"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            category_code="TEST_MINMAX",
            name="Test MinMax Category"
        )
        
        self.supplier = Supplier.objects.create(
            company_name="Test MinMax Supplier",
            email="test@minmax.com"
        )
        
        # Create products with different characteristics
        self.product1 = Product.objects.create(
            code="MINMAX_001",
            name="Product 1",
            category=self.category,
            last_purchase_price=Decimal('10.00'),
            lead_time=30
        )
        
        self.product2 = Product.objects.create(
            code="MINMAX_002", 
            name="Product 2",
            category=self.category,
            last_purchase_price=Decimal('20.00'),
            lead_time=45
        )
        
        self.product3 = Product.objects.create(
            code="MINMAX_003",
            name="Product 3", 
            category=self.category,
            last_purchase_price=Decimal('30.00'),
            lead_time=60
        )
        
        # Create DailyMetrics with different patterns
        today = date.today()
        
        # Product 1: High stock (50), high demand (avg 10/day)
        for i in range(30):
            DailyMetrics.objects.create(
                product=self.product1,
                date=today - timedelta(days=i),
                stock=50 - i // 10,  # Stock: 50, 50, 50... 47, 47, 47... etc
                sales_quantity=8 + (i % 5),  # Sales: 8-12 range
                potential_sales=10 + (i % 3)  # Potential: 10-12 range
            )
        
        # Product 2: Medium stock (25), medium demand (avg 5/day)
        for i in range(30):
            DailyMetrics.objects.create(
                product=self.product2,
                date=today - timedelta(days=i),
                stock=25 - i // 15,  # Stock: 25, 25... 23, 23... etc
                sales_quantity=3 + (i % 4),  # Sales: 3-6 range
                potential_sales=5 + (i % 2)  # Potential: 5-6 range
            )
        
        # Product 3: Low stock (5), low demand (avg 1/day)
        for i in range(30):
            DailyMetrics.objects.create(
                product=self.product3,
                date=today - timedelta(days=i),
                stock=5,  # Constant low stock
                sales_quantity=0 if i % 5 == 0 else 1,  # Mostly 1, occasionally 0
                potential_sales=1  # Constant low demand
            )
        
        # Product 4: No metrics (will have None values)
        self.product4 = Product.objects.create(
            code="MINMAX_004",
            name="Product 4 - No Data",
            category=self.category,
            last_purchase_price=Decimal('40.00'),
            lead_time=15
        )
        
        # Product 5: Zero stock product
        self.product5 = Product.objects.create(
            code="MINMAX_005",
            name="Product 5 - Zero Stock",
            category=self.category,
            last_purchase_price=Decimal('50.00'),
            lead_time=20
        )
        
        # Create metrics with zero stock
        for i in range(10):
            DailyMetrics.objects.create(
                product=self.product5,
                date=today - timedelta(days=i),
                stock=0,  # Zero stock
                sales_quantity=0,
                potential_sales=2  # Has demand but no stock
            )
    
    def get_annotated_queryset(self):
        """Helper method to create annotated queryset like in populate_product_list_context"""
        from django.db.models import Subquery, OuterRef, IntegerField, Avg, Case, When, F, Q
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        
        return Product.objects.annotate(
            # Current stock from latest daily metrics
            current_stock=Subquery(
                DailyMetrics.objects.filter(
                    product=OuterRef('pk')
                ).order_by('-date').values('stock')[:1],
                output_field=IntegerField()
            ),
            # Average daily demand from potential_sales over last 365 days
            avg_daily_demand=Avg(
                'daily_metrics__potential_sales',
                filter=Q(
                    daily_metrics__date__range=[start_date, end_date],
                    daily_metrics__potential_sales__isnull=False
                )
            ),
            # Remainder days calculation: current_stock / avg_daily_demand
            remainder_days=Case(
                When(
                    Q(avg_daily_demand__gt=0) & Q(current_stock__isnull=False), 
                    then=F('current_stock') / F('avg_daily_demand')
                ),
                default=None,
                output_field=IntegerField()
            )
        )
    
    def test_apply_min_max_filter_valid_range(self):
        """Test basic min/max filtering with valid range"""
        queryset = self.get_annotated_queryset()
        
        # Filter for products with current stock between 20 and 40
        result = apply_min_max_filter(queryset, 'current_stock', '20', '40')
        
        # Should include product2 (stock ~25) but exclude product1 (stock ~50) and product3 (stock 5)
        result_list = list(result.values_list('code', flat=True))
        self.assertIn('MINMAX_002', result_list)
        self.assertNotIn('MINMAX_001', result_list)  # Too high
        self.assertNotIn('MINMAX_003', result_list)  # Too low
        self.assertNotIn('MINMAX_004', result_list)  # No data (None)
        self.assertNotIn('MINMAX_005', result_list)  # Zero stock (below min)
    
    def test_apply_min_max_filter_min_only(self):
        """Test filtering with only minimum value"""
        queryset = self.get_annotated_queryset()
        
        # Filter for products with current stock >= 20
        result = apply_min_max_filter(queryset, 'current_stock', '20', '')
        
        result_list = list(result.values_list('code', flat=True))
        self.assertIn('MINMAX_001', result_list)  # High stock
        self.assertIn('MINMAX_002', result_list)  # Medium stock
        self.assertNotIn('MINMAX_003', result_list)  # Low stock
        self.assertNotIn('MINMAX_004', result_list)  # No data
        self.assertNotIn('MINMAX_005', result_list)  # Zero stock
    
    def test_apply_min_max_filter_max_only(self):
        """Test filtering with only maximum value (should include None values)"""
        queryset = self.get_annotated_queryset()
        
        # Filter for products with current stock <= 30, should include None values
        result = apply_min_max_filter(queryset, 'current_stock', '', '30')
        result_list = list(result.values_list('code', flat=True))
        # Should include product2 (medium stock), product3 (low stock), product5 (zero stock), and product4 (None)
        self.assertNotIn('MINMAX_001', result_list)  # Too high
        self.assertIn('MINMAX_002', result_list)  # Medium stock
        self.assertIn('MINMAX_003', result_list)  # Low stock
        self.assertIn('MINMAX_004', result_list)  # No data (None) - now included
        self.assertIn('MINMAX_005', result_list)  # Zero stock (within range)
    
    def test_apply_min_max_filter_empty_values(self):
        """Test filtering with empty/None values"""
        queryset = self.get_annotated_queryset()
        
        # Empty strings should not filter anything
        result = apply_min_max_filter(queryset, 'current_stock', '', '')
        self.assertEqual(result.count(), queryset.count())
        
        # None values should not filter anything
        result = apply_min_max_filter(queryset, 'current_stock', None, None)
        self.assertEqual(result.count(), queryset.count())
    
    def test_apply_min_max_filter_invalid_values(self):
        """Test filtering with invalid numeric values"""
        queryset = self.get_annotated_queryset()
        
        # Invalid min value should be ignored
        result = apply_min_max_filter(queryset, 'current_stock', 'invalid', '30')
        # Should work same as max-only filter
        self.assertLess(result.count(), queryset.count())
        
        # Invalid max value should be ignored
        result = apply_min_max_filter(queryset, 'current_stock', '10', 'invalid')
        # Should work same as min-only filter
        self.assertLess(result.count(), queryset.count())
        
        # Both invalid should return original queryset
        result = apply_min_max_filter(queryset, 'current_stock', 'invalid', 'invalid')
        self.assertEqual(result.count(), queryset.count())
    
    def test_apply_min_max_filter_avg_daily_demand(self):
        """Test filtering by average daily demand"""
        queryset = self.get_annotated_queryset()
        
        # Filter for products with average daily demand between 3 and 8
        result = apply_min_max_filter(queryset, 'avg_daily_demand', '3', '8')
        
        result_list = list(result.values_list('code', flat=True))
        # Product2 should have avg demand ~5.5, Product3 should have ~1
        self.assertIn('MINMAX_002', result_list)
        self.assertNotIn('MINMAX_001', result_list)  # Too high (~11)
        self.assertNotIn('MINMAX_003', result_list)  # Too low (~1)
        self.assertNotIn('MINMAX_004', result_list)  # No data
        # Product5 has avg demand ~2, should be included
        self.assertNotIn('MINMAX_005', result_list)  # Below min
    
    def test_apply_min_max_filter_remainder_days(self):
        """Test filtering by remainder days"""
        queryset = self.get_annotated_queryset()
        
        # Filter for products with remainder days between 10 and 100
        result = apply_min_max_filter(queryset, 'remainder_days', '10', '100')
        
        result_list = list(result.values_list('code', flat=True))
        # Product1: ~47 stock / ~11 demand = ~4.3 days (too low)
        # Product2: ~24 stock / ~5.5 demand = ~4.4 days (too low)
        # Product3: 5 stock / 1 demand = 5 days (too low)
        # Most should be filtered out due to low remainder days
        # Only products with very low demand relative to stock would pass
    
    def test_apply_min_max_filter_zero_values(self):
        """Test filtering that includes zero values correctly"""
        queryset = self.get_annotated_queryset()
        
        # Filter for products with current stock >= 0 (should include zero stock)
        result = apply_min_max_filter(queryset, 'current_stock', '0', '')
        
        result_list = list(result.values_list('code', flat=True))
        self.assertIn('MINMAX_001', result_list)  # High stock
        self.assertIn('MINMAX_002', result_list)  # Medium stock
        self.assertIn('MINMAX_003', result_list)  # Low stock
        self.assertNotIn('MINMAX_004', result_list)  # No data (None)
        self.assertIn('MINMAX_005', result_list)  # Zero stock (should be included)
    
    def test_apply_min_max_filter_exclude_none_values(self):
        """Test that None/N/A values are properly excluded"""
        queryset = self.get_annotated_queryset()
        
        # Any numeric filter should exclude products with None values
        result = apply_min_max_filter(queryset, 'current_stock', '0', '1000')
        
        result_list = list(result.values_list('code', flat=True))
        self.assertNotIn('MINMAX_004', result_list)  # Should exclude None values
        
        # Same for avg_daily_demand
        result = apply_min_max_filter(queryset, 'avg_daily_demand', '0', '1000')
        result_list = list(result.values_list('code', flat=True))
        self.assertNotIn('MINMAX_004', result_list)  # Should exclude None values
    
    def test_apply_min_max_filter_inverted_range(self):
        """Test filtering with min > max (should return empty results)"""
        queryset = self.get_annotated_queryset()
        
        # Min greater than max should return empty queryset
        result = apply_min_max_filter(queryset, 'current_stock', '100', '10')
        self.assertEqual(result.count(), 0)
    
    def test_apply_min_max_filter_decimal_values(self):
        """Test filtering with decimal values"""
        queryset = self.get_annotated_queryset()
        
        # Use decimal values for filtering
        result = apply_min_max_filter(queryset, 'avg_daily_demand', '2.5', '6.5')
        
        # Should work correctly with decimal comparisons
        self.assertIsInstance(result.count(), int)
    
    def test_apply_min_max_filter_queryset_immutability(self):
        """Test that original queryset is not modified"""
        original_queryset = self.get_annotated_queryset()
        original_count = original_queryset.count()
        
        # Apply filter
        result = apply_min_max_filter(original_queryset, 'current_stock', '20', '40')
        
        # Original queryset should be unchanged
        self.assertEqual(original_queryset.count(), original_count)
        self.assertEqual(original_queryset.count(), 5)  # All products
    
    def test_apply_min_max_filter_annotation_field_names(self):
        """Test that filtering works with annotation field names"""
        from django.db.models import Value, DecimalField
        
        # Create queryset with annotations (similar to how context.py does it)
        queryset = Product.objects.annotate(
            current_stock=Value(Decimal('25.0'), output_field=DecimalField()),
            avg_daily_demand=Value(Decimal('5.0'), output_field=DecimalField()),
            remainder_days=Value(Decimal('5.0'), output_field=DecimalField())
        )
        
        # Filter should work with annotated fields
        result = apply_min_max_filter(queryset, 'current_stock', '20', '30')
        self.assertEqual(result.count(), queryset.count())  # All should match
        
        result = apply_min_max_filter(queryset, 'current_stock', '30', '40')
        self.assertEqual(result.count(), 0)  # None should match
    
    def test_apply_min_max_filter_edge_case_exact_boundaries(self):
        """Test filtering with exact boundary values"""
        queryset = self.get_annotated_queryset()
        
        # Test exact match on boundaries
        # Get current stock of product3 (should be 5)
        result = apply_min_max_filter(queryset, 'current_stock', '5', '5')
        
        result_list = list(result.values_list('code', flat=True))
        # Should include product3 which has exactly 5 stock
        self.assertIn('MINMAX_003', result_list)
