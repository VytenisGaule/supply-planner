from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock
from decimal import Decimal
import random
import string
from app.models import User, Category, Product, Supplier


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False
        }
    
    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_user_str_method(self):
        """Test User __str__ method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')
        
        # Test with None username
        user.username = None
        self.assertEqual(str(user), 'N/A')
    
    def test_user_without_removed_fields(self):
        """Test that removed fields are not accessible"""
        user = User.objects.create_user(**self.user_data)
        
        # These fields should be None (removed)
        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)
        # Email is now available (kept from AbstractUser)
        self.assertIsNotNone(user.email)  # Email should exist


class CategoryModelTest(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        """Set up test data"""
        # Create root categories
        self.electronics = Category.objects.create(
            category_code='ELEC',
            name='Electronics',
            description='Electronic devices'
        )
        
        self.furniture = Category.objects.create(
            category_code='FURN',
            name='Furniture',
            description='Home and office furniture'
        )
        
        # Create subcategories
        self.computers = Category.objects.create(
            category_code='COMP',
            name='Computers',
            description='Computing devices',
            parent=self.electronics
        )
        
        self.laptops = Category.objects.create(
            category_code='LAP',
            name='Laptops',
            description='Portable computers',
            parent=self.computers
        )
        
        self.gaming_laptops = Category.objects.create(
            category_code='GAMLAP',
            name='Gaming Laptops',
            description='High-performance gaming laptops',
            parent=self.laptops
        )
    
    def test_category_str_method(self):
        """Test Category __str__ method"""
        # Root category should return name
        self.assertEqual(str(self.electronics), 'Electronics')
        
        # Subcategory should return parent > child
        self.assertEqual(str(self.computers), 'Electronics > Computers')
        self.assertEqual(str(self.laptops), 'Electronics > Computers > Laptops')
    
    def test_category_level_auto_calculation(self):
        """Test that category levels are calculated automatically"""
        self.assertEqual(self.electronics.level, 0)  # Root
        self.assertEqual(self.computers.level, 1)    # Level 1
        self.assertEqual(self.laptops.level, 2)      # Level 2
        self.assertEqual(self.gaming_laptops.level, 3)  # Level 3
    
    def test_is_root_property(self):
        """Test is_root property"""
        self.assertTrue(self.electronics.is_root)
        self.assertTrue(self.furniture.is_root)
        self.assertFalse(self.computers.is_root)
        self.assertFalse(self.laptops.is_root)
    
    def test_is_leaf_property(self):
        """Test is_leaf property"""
        self.assertTrue(self.gaming_laptops.is_leaf)  # No subcategories
        self.assertTrue(self.furniture.is_leaf)       # No subcategories
        self.assertFalse(self.electronics.is_leaf)    # Has subcategories
        self.assertFalse(self.computers.is_leaf)      # Has subcategories
    
    def test_get_path_method(self):
        """Test get_path method"""
        self.assertEqual(self.electronics.get_path(), 'Electronics')
        self.assertEqual(self.computers.get_path(), 'Electronics > Computers')
        self.assertEqual(self.laptops.get_path(), 'Electronics > Computers > Laptops')
        self.assertEqual(self.gaming_laptops.get_path(), 'Electronics > Computers > Laptops > Gaming Laptops')
    
    def test_get_descendants_method(self):
        """Test get_descendants method"""
        # Electronics should have all subcategories
        electronics_descendants = self.electronics.get_descendants()
        self.assertIn(self.computers, electronics_descendants)
        self.assertIn(self.laptops, electronics_descendants)
        self.assertIn(self.gaming_laptops, electronics_descendants)
        self.assertEqual(len(electronics_descendants), 3)
        
        # Computers should have laptops and gaming laptops
        computers_descendants = self.computers.get_descendants()
        self.assertIn(self.laptops, computers_descendants)
        self.assertIn(self.gaming_laptops, computers_descendants)
        self.assertEqual(len(computers_descendants), 2)
        
        # Gaming laptops should have no descendants
        gaming_descendants = self.gaming_laptops.get_descendants()
        self.assertEqual(len(gaming_descendants), 0)
    
    def test_unique_constraints(self):
        """Test unique constraints"""
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Category.objects.create(
                    category_code='ELEC',  # Duplicate code
                    name='Electronics Duplicate'
                )
        
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Category.objects.create(
                    category_code='ELEC2',
                    name='Electronics'  # Duplicate name
                )


class SupplierModelTest(TestCase):
    """Test cases for Supplier model"""
    
    def setUp(self):
        """Set up test data"""
        self.supplier1 = Supplier.objects.create(
            company_name='Tech Corp',
            email='contact@techcorp.com'
        )
        
        self.supplier2 = Supplier.objects.create(
            company_name='Supply Co',
            email='info@supplyco.com'
        )
        
        self.supplier3 = Supplier.objects.create(
            company_name='No Email Supplier'
            # No email provided
        )
    
    def test_supplier_str_method(self):
        """Test Supplier __str__ method"""
        self.assertEqual(str(self.supplier1), 'Tech Corp')
        self.assertEqual(str(self.supplier3), 'No Email Supplier')
        
        # Test with None company_name
        supplier = Supplier(company_name=None)
        self.assertEqual(str(supplier), '')
    
    def test_supplier_creation(self):
        """Test supplier creation with and without email"""
        # With email
        self.assertEqual(self.supplier1.company_name, 'Tech Corp')
        self.assertEqual(self.supplier1.email, 'contact@techcorp.com')
        
        # Without email
        self.assertEqual(self.supplier3.company_name, 'No Email Supplier')
        self.assertIsNone(self.supplier3.email)


class ProductModelTest(TestCase):
    """Test cases for Product model"""
    
    def setUp(self):
        """Set up test data"""
        # Create categories
        self.electronics = Category.objects.create(
            category_code='ELEC',
            name='Electronics'
        )
        
        self.laptops = Category.objects.create(
            category_code='LAP',
            name='Laptops',
            parent=self.electronics
        )
        
        # Create suppliers
        self.supplier1 = Supplier.objects.create(
            company_name='Tech Corp',
            email='contact@techcorp.com'
        )
        
        self.supplier2 = Supplier.objects.create(
            company_name='Supply Co',
            email='info@supplyco.com'
        )
        
        # Create products
        self.product1 = Product.objects.create(
            kodas='LAP001',
            pavadinimas='Gaming Laptop',
            category=self.laptops,
            last_purchase_price=1299.99,
            currency='USD'
        )
        
        self.product2 = Product.objects.create(
            kodas='LAP002',
            pavadinimas='Business Laptop',
            category=self.laptops,
            last_purchase_price=899.50,
            currency='EUR'
        )
        
        # Product without kodas
        self.product3 = Product.objects.create(
            pavadinimas='Unnamed Product',
            category=self.electronics
        )
        
        # Add suppliers to products
        self.product1.suppliers.add(self.supplier1, self.supplier2)
        self.product2.suppliers.add(self.supplier1)
    
    def test_product_str_method(self):
        """Test Product __str__ method"""
        self.assertEqual(str(self.product1), 'LAP001 - Gaming Laptop')
        self.assertEqual(str(self.product2), 'LAP002 - Business Laptop')
        self.assertEqual(str(self.product3), 'None - Unnamed Product')
    
    def test_kodas_unique_constraint(self):
        """Test that kodas is unique when not blank"""
        # This should work - blank kodas is allowed
        Product.objects.create(
            pavadinimas='Another Unnamed Product'
        )
        
        # This should fail - duplicate kodas
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                kodas='LAP001',  # Duplicate
                pavadinimas='Duplicate Laptop'
            )
    
    def test_multiple_blank_kodas_allowed(self):
        """Test that multiple products with blank kodas are allowed"""
        product4 = Product.objects.create(pavadinimas='Product 4')
        product5 = Product.objects.create(pavadinimas='Product 5')
        
        # Both should exist
        self.assertTrue(Product.objects.filter(pavadinimas='Product 4').exists())
        self.assertTrue(Product.objects.filter(pavadinimas='Product 5').exists())
    
    def test_currency_choices(self):
        """Test currency field choices"""
        self.assertEqual(self.product1.currency, 'USD')
        self.assertEqual(self.product2.currency, 'EUR')
        
        # Test default currency
        product = Product.objects.create(
            kodas='TEST001',
            pavadinimas='Test Product'
        )
        self.assertEqual(product.currency, 'USD')  # Default
    
    def test_supplier_relationships(self):
        """Test many-to-many relationship with suppliers"""
        # Product1 has 2 suppliers
        self.assertEqual(self.product1.suppliers.count(), 2)
        self.assertIn(self.supplier1, self.product1.suppliers.all())
        self.assertIn(self.supplier2, self.product1.suppliers.all())
        
        # Product2 has 1 supplier
        self.assertEqual(self.product2.suppliers.count(), 1)
        self.assertIn(self.supplier1, self.product2.suppliers.all())
        
        # Product3 has no suppliers
        self.assertEqual(self.product3.suppliers.count(), 0)
        
        # Check reverse relationship
        self.assertEqual(self.supplier1.products.count(), 2)
        self.assertEqual(self.supplier2.products.count(), 1)
    
    def test_category_relationship(self):
        """Test relationship with categories"""
        self.assertEqual(self.product1.category, self.laptops)
        self.assertEqual(self.product2.category, self.laptops)
        self.assertEqual(self.product3.category, self.electronics)
        
        # Test category's products (reverse relationship)
        laptops_products = self.laptops.products.all()
        self.assertIn(self.product1, laptops_products)
        self.assertIn(self.product2, laptops_products)
        self.assertEqual(laptops_products.count(), 2)


class CategoryProductRelationshipTest(TestCase):
    """Test cases for Category-Product relationships and methods"""
    
    def setUp(self):
        """Set up complex category hierarchy with products"""
        # Create category hierarchy
        self.electronics = Category.objects.create(
            category_code='ELEC',
            name='Electronics'
        )
        
        self.computers = Category.objects.create(
            category_code='COMP',
            name='Computers',
            parent=self.electronics
        )
        
        self.laptops = Category.objects.create(
            category_code='LAP',
            name='Laptops',
            parent=self.computers
        )
        
        self.gaming_laptops = Category.objects.create(
            category_code='GAMLAP',
            name='Gaming Laptops',
            parent=self.laptops
        )
        
        # Create products at different levels
        self.general_electronics = Product.objects.create(
            kodas='GEN001',
            pavadinimas='General Electronic Device',
            category=self.electronics
        )
        
        self.desktop = Product.objects.create(
            kodas='DESK001',
            pavadinimas='Desktop Computer',
            category=self.computers
        )
        
        self.business_laptop = Product.objects.create(
            kodas='BUS001',
            pavadinimas='Business Laptop',
            category=self.laptops
        )
        
        self.gaming_laptop1 = Product.objects.create(
            kodas='GAM001',
            pavadinimas='Gaming Laptop Pro',
            category=self.gaming_laptops
        )
        
        self.gaming_laptop2 = Product.objects.create(
            kodas='GAM002',
            pavadinimas='Gaming Laptop Elite',
            category=self.gaming_laptops
        )
    
    def test_get_all_products_method(self):
        """Test Category.get_all_products() method"""
        # Electronics should include all products
        all_electronics = self.electronics.get_all_products()
        self.assertEqual(all_electronics.count(), 5)
        self.assertIn(self.general_electronics, all_electronics)
        self.assertIn(self.desktop, all_electronics)
        self.assertIn(self.business_laptop, all_electronics)
        self.assertIn(self.gaming_laptop1, all_electronics)
        self.assertIn(self.gaming_laptop2, all_electronics)
        
        # Computers should include desktop + all laptop products
        all_computers = self.computers.get_all_products()
        self.assertEqual(all_computers.count(), 4)
        self.assertIn(self.desktop, all_computers)
        self.assertIn(self.business_laptop, all_computers)
        self.assertIn(self.gaming_laptop1, all_computers)
        self.assertIn(self.gaming_laptop2, all_computers)
        self.assertNotIn(self.general_electronics, all_computers)
        
        # Laptops should include business laptop + gaming laptops
        all_laptops = self.laptops.get_all_products()
        self.assertEqual(all_laptops.count(), 3)
        self.assertIn(self.business_laptop, all_laptops)
        self.assertIn(self.gaming_laptop1, all_laptops)
        self.assertIn(self.gaming_laptop2, all_laptops)
        
        # Gaming laptops should only include gaming products
        gaming_products = self.gaming_laptops.get_all_products()
        self.assertEqual(gaming_products.count(), 2)
        self.assertIn(self.gaming_laptop1, gaming_products)
        self.assertIn(self.gaming_laptop2, gaming_products)


class ModelIntegrationTest(TestCase):
    """Integration tests for all models working together"""
    
    def setUp(self):
        """Set up comprehensive test scenario"""
        # Create user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create category hierarchy
        self.electronics = Category.objects.create(
            category_code='ELEC',
            name='Electronics'
        )
        
        self.laptops = Category.objects.create(
            category_code='LAP',
            name='Laptops',
            parent=self.electronics
        )
        
        # Create suppliers
        self.supplier1 = Supplier.objects.create(
            company_name='TechCorp Inc',
            email='sales@techcorp.com'
        )
        
        self.supplier2 = Supplier.objects.create(
            company_name='Hardware Solutions',
            email='orders@hwsolutions.com'
        )
        
        # Create products with relationships
        self.laptop1 = Product.objects.create(
            kodas='LAP2024001',
            pavadinimas='Professional Laptop',
            category=self.laptops,
            last_purchase_price=1599.99,
            currency='USD'
        )
        
        self.laptop2 = Product.objects.create(
            kodas='LAP2024002',
            pavadinimas='Budget Laptop',
            category=self.laptops,
            last_purchase_price=799.50,
            currency='EUR'
        )
        
        # Associate suppliers with products
        self.laptop1.suppliers.add(self.supplier1, self.supplier2)
        self.laptop2.suppliers.add(self.supplier2)
    
    def test_complete_data_integrity(self):
        """Test that all relationships work correctly"""
        # Test category hierarchy
        self.assertEqual(self.laptops.parent, self.electronics)
        self.assertEqual(self.laptops.level, 1)
        self.assertEqual(self.electronics.level, 0)
        
        # Test product-category relationships
        laptop_products = self.laptops.products.all()
        self.assertEqual(laptop_products.count(), 2)
        self.assertIn(self.laptop1, laptop_products)
        self.assertIn(self.laptop2, laptop_products)
        
        # Test product-supplier relationships
        self.assertEqual(self.laptop1.suppliers.count(), 2)
        self.assertEqual(self.laptop2.suppliers.count(), 1)
        self.assertEqual(self.supplier1.products.count(), 1)
        self.assertEqual(self.supplier2.products.count(), 2)
        
        # Test get_all_products with hierarchy
        all_electronics = self.electronics.get_all_products()
        self.assertEqual(all_electronics.count(), 2)
        self.assertIn(self.laptop1, all_electronics)
        self.assertIn(self.laptop2, all_electronics)
    
    def test_cascade_behavior(self):
        """Test cascade deletion behavior"""
        # Delete parent category should delete child
        laptop_id = self.laptops.id
        self.electronics.delete()
        
        # Child category should be deleted (CASCADE)
        self.assertFalse(Category.objects.filter(id=laptop_id).exists())
        
        # Products should still exist but have null category (SET_NULL)
        self.assertTrue(Product.objects.filter(id=self.laptop1.id).exists())
        self.laptop1.refresh_from_db()
        self.assertIsNone(self.laptop1.category)
    
    def test_data_validation(self):
        """Test various data validation scenarios"""
        # Test unique kodas constraint
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Product.objects.create(
                    kodas='LAP2024001',  # Duplicate
                    pavadinimas='Duplicate Product'
                )
        
        # Test that blank kodas is allowed
        product_no_code = Product.objects.create(
            kodas='',  # Use empty string instead of duplicate
            pavadinimas='Product Without Code'
        )
        self.assertEqual(product_no_code.kodas, '')
        
        # Test currency choices
        product_usd = Product.objects.create(
            kodas='TEST999',  # Use unique code
            pavadinimas='USD Product',
            currency='USD'
        )
        self.assertEqual(product_usd.currency, 'USD')


class MockDataFactory:
    """Factory class for generating mock test data"""
    
    @staticmethod
    def random_string(length=10):
        """Generate random string of specified length"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email():
        """Generate random email address"""
        username = MockDataFactory.random_string(8)
        domain = random.choice(['gmail.com', 'yahoo.com', 'company.com', 'test.org'])
        return f"{username}@{domain}"
    
    @staticmethod
    def random_price():
        """Generate random price between 10 and 5000"""
        return round(random.uniform(10.0, 5000.0), 2)
    
    @staticmethod
    def create_mock_user(username=None, **kwargs):
        """Create a mock user with optional parameters"""
        if username is None:
            username = f"user_{MockDataFactory.random_string(6)}"
        
        default_data = {
            'username': username,
            'email': MockDataFactory.random_email(),
            'password': 'testpass123',
            'is_active': True,
            'is_staff': random.choice([True, False]),
            'is_superuser': False
        }
        default_data.update(kwargs)
        
        return User.objects.create_user(**default_data)
    
    @staticmethod
    def create_mock_category(parent=None, **kwargs):
        """Create a mock category with optional parent"""
        code_suffix = MockDataFactory.random_string(4)
        name_suffix = MockDataFactory.random_string(6)
        
        default_data = {
            'category_code': f"CAT_{code_suffix}",
            'name': f"Category {name_suffix}",
            'description': f"Description for category {name_suffix}",
            'parent': parent
        }
        default_data.update(kwargs)
        return Category.objects.create(**default_data)
    
    @staticmethod
    def create_mock_supplier(**kwargs):
        """Create a mock supplier"""
        company_suffix = MockDataFactory.random_string(6)
        
        default_data = {
            'company_name': f"Company {company_suffix}",
            'email': MockDataFactory.random_email()
        }
        default_data.update(kwargs)
        return Supplier.objects.create(**default_data)
    
    @staticmethod
    def create_mock_product(category=None, suppliers=None, **kwargs):
        """Create a mock product with optional relationships"""
        code_suffix = MockDataFactory.random_string(6)
        name_suffix = MockDataFactory.random_string(8)
        
        default_data = {
            'kodas': f"PROD_{code_suffix}",
            'pavadinimas': f"Product {name_suffix}",
            'category': category,
            'last_purchase_price': Decimal(str(MockDataFactory.random_price())),
            'currency': random.choice(['USD', 'EUR'])
        }
        default_data.update(kwargs)
        
        product = Product.objects.create(**default_data)
        
        if suppliers:
            if isinstance(suppliers, list):
                product.suppliers.add(*suppliers)
            else:
                product.suppliers.add(suppliers)
        
        return product


class MockDataTestCase(TestCase):
    """Test cases using mock data factory"""
    
    def test_mock_user_creation(self):
        """Test creating users with mock data"""
        # Create 5 random users
        users = []
        for i in range(5):
            user = MockDataFactory.create_mock_user()
            users.append(user)
            self.assertTrue(user.username.startswith('user_'))
            self.assertTrue(user.is_active)
        
        # Ensure all users are unique
        usernames = [user.username for user in users]
        self.assertEqual(len(usernames), len(set(usernames)))
    
    def test_mock_category_hierarchy(self):
        """Test creating category hierarchy with mock data"""
        # Create root categories
        root1 = MockDataFactory.create_mock_category()
        root2 = MockDataFactory.create_mock_category()
        
        # Create subcategories
        sub1 = MockDataFactory.create_mock_category(parent=root1)
        sub2 = MockDataFactory.create_mock_category(parent=root1)
        sub_sub = MockDataFactory.create_mock_category(parent=sub1)
        
        # Test hierarchy
        self.assertTrue(root1.is_root)
        self.assertTrue(root2.is_root)
        self.assertFalse(sub1.is_root)
        self.assertFalse(sub_sub.is_root)
        
        # Test levels
        self.assertEqual(root1.level, 0)
        self.assertEqual(sub1.level, 1)
        self.assertEqual(sub_sub.level, 2)
        
        # Test descendants
        descendants = root1.get_descendants()
        self.assertIn(sub1, descendants)
        self.assertIn(sub2, descendants)
        self.assertIn(sub_sub, descendants)
    
    def test_mock_supplier_creation(self):
        """Test creating suppliers with mock data"""
        suppliers = []
        for i in range(10):
            supplier = MockDataFactory.create_mock_supplier()
            suppliers.append(supplier)
            self.assertTrue(supplier.company_name.startswith('Company'))
            self.assertIn('@', supplier.email)
        
        # Test unique company names
        company_names = [s.company_name for s in suppliers]
        self.assertEqual(len(company_names), len(set(company_names)))
    
    def test_mock_product_with_relationships(self):
        """Test creating products with relationships using mock data"""
        # Create dependencies
        category = MockDataFactory.create_mock_category()
        supplier1 = MockDataFactory.create_mock_supplier()
        supplier2 = MockDataFactory.create_mock_supplier()
        
        # Create product with relationships
        product = MockDataFactory.create_mock_product(
            category=category,
            suppliers=[supplier1, supplier2]
        )
        
        self.assertEqual(product.category, category)
        self.assertEqual(product.suppliers.count(), 2)
        self.assertIn(supplier1, product.suppliers.all())
        self.assertIn(supplier2, product.suppliers.all())
        self.assertIn(product.currency, ['USD', 'EUR'])
    
    def test_bulk_mock_data_creation(self):
        """Test creating large amounts of mock data"""
        # Create category hierarchy
        electronics = MockDataFactory.create_mock_category(
            category_code='ELECTRONICS',
            name='Electronics'
        )
        computers = MockDataFactory.create_mock_category(
            parent=electronics,
            category_code='COMPUTERS',
            name='Computers'
        )
        
        # Create suppliers
        suppliers = []
        for i in range(5):
            suppliers.append(MockDataFactory.create_mock_supplier())
        
        # Create products
        products = []
        for i in range(20):
            category = random.choice([electronics, computers])
            product_suppliers = random.sample(suppliers, k=random.randint(1, 3))
            
            product = MockDataFactory.create_mock_product(
                category=category,
                suppliers=product_suppliers
            )
            products.append(product)
        
        # Verify data integrity
        self.assertEqual(Product.objects.count(), 20)
        self.assertEqual(Supplier.objects.count(), 5)
        self.assertEqual(Category.objects.count(), 2)
        
        # Test that all products have suppliers
        for product in products:
            self.assertGreaterEqual(product.suppliers.count(), 1)
            self.assertLessEqual(product.suppliers.count(), 3)


class AdvancedModelTestCase(TestCase):
    """Advanced test cases with edge cases and error handling"""
    
    def test_category_circular_reference_prevention(self):
        """Test that circular references in categories are handled"""
        # Create categories
        cat1 = MockDataFactory.create_mock_category()
        cat2 = MockDataFactory.create_mock_category(parent=cat1)
        
        # Attempt to create circular reference
        # This should be prevented at the application level
        # (Note: Django doesn't prevent this at DB level by default)
        cat1.parent = cat2
        
        # In a real application, you'd want to add validation to prevent this
        # For now, we'll just verify the structure
        with self.assertRaises(Exception):
            # This would create infinite recursion in get_path()
            # We can test this by calling get_path() after creating the circular ref
            cat1.save()
            cat1.get_path()  # This should fail with recursion
    
    def test_product_price_edge_cases(self):
        """Test product price handling with edge cases"""
        category = MockDataFactory.create_mock_category()
        
        # Test with zero price
        product_zero = Product.objects.create(
            kodas='ZERO001',
            pavadinimas='Zero Price Product',
            category=category,
            last_purchase_price=Decimal('0.0000'),
            currency='USD'
        )
        self.assertEqual(product_zero.last_purchase_price, Decimal('0.0000'))
        
        # Test with very high precision
        product_precise = Product.objects.create(
            kodas='PRECISE001',
            pavadinimas='High Precision Product',
            category=category,
            last_purchase_price=Decimal('1234.5678'),
            currency='EUR'
        )
        self.assertEqual(product_precise.last_purchase_price, Decimal('1234.5678'))
        
        # Test with None price
        product_no_price = Product.objects.create(
            kodas='NOPRICE001',
            pavadinimas='No Price Product',
            category=category
        )
        self.assertIsNone(product_no_price.last_purchase_price)
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        # Create category with unicode characters
        unicode_category = Category.objects.create(
            category_code='UNICODE001',
            name='Kategorija ąčęėįšųū žĮĄČĖĘ',
            description='Aprašymas su lietuviškomis raidėmis'
        )
        
        # Create supplier with special characters
        special_supplier = Supplier.objects.create(
            company_name='Компания "Тест" & Co.',
            email='test@ünicöde-dömaín.com'
        )
        
        # Create product with unicode name
        unicode_product = Product.objects.create(
            kodas='UNICODE002',
            pavadinimas='Produktas ąčęėįšųū 中文 العربية',
            category=unicode_category,
            last_purchase_price=Decimal('999.99'),
            currency='EUR'
        )
        unicode_product.suppliers.add(special_supplier)
        
        # Test string representations
        self.assertIn('Kategorija', str(unicode_category))
        self.assertIn('Компания', str(special_supplier))
        self.assertIn('Produktas', str(unicode_product))
    
    def test_long_text_fields(self):
        """Test handling of very long text in fields"""
        # Create category with maximum length description
        long_description = 'A' * 1000  # Very long description
        
        long_category = Category.objects.create(
            category_code='LONG001',
            name='Category with Long Description',
            description=long_description
        )
        
        # Create product with maximum length name
        long_name = 'B' * 400  # Maximum length for pavadinimas
        
        long_product = Product.objects.create(
            kodas='LONG002',
            pavadinimas=long_name,
            category=long_category
        )
        
        self.assertEqual(len(long_category.description), 1000)
        self.assertEqual(len(long_product.pavadinimas), 400)


class DatabaseTransactionTestCase(TransactionTestCase):
    """Test cases that require database transactions"""
    
    def test_concurrent_product_creation(self):
        """Test concurrent product creation with same kodas"""
        category = MockDataFactory.create_mock_category()
        
        def create_product_with_code(kodas):
            return Product.objects.create(
                kodas=kodas,
                pavadinimas=f'Product {kodas}',
                category=category
            )
        
        # First product should succeed
        product1 = create_product_with_code('CONCURRENT001')
        self.assertIsNotNone(product1.id)
        
        # Second product with same kodas should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_product_with_code('CONCURRENT001')
    
    def test_bulk_operations_performance(self):
        """Test bulk operations for performance"""
        category = MockDataFactory.create_mock_category()
        suppliers = [MockDataFactory.create_mock_supplier() for _ in range(5)]
        
        # Bulk create products
        products_data = []
        for i in range(100):
            products_data.append(Product(
                kodas=f'BULK{i:03d}',
                pavadinimas=f'Bulk Product {i}',
                category=category,
                last_purchase_price=Decimal(str(MockDataFactory.random_price())),
                currency=random.choice(['USD', 'EUR'])
            ))
        
        # Measure bulk creation
        products = Product.objects.bulk_create(products_data)
        self.assertEqual(len(products), 100)
        
        # Verify all products were created
        self.assertEqual(Product.objects.filter(kodas__startswith='BULK').count(), 100)


class MockedExternalServiceTestCase(TestCase):
    """Test cases with mocked external services"""
    
    def test_currency_conversion_mock(self):
        """Test currency conversion with mocked exchange rate service"""
        # Note: This is a placeholder test for future currency conversion functionality
        category = MockDataFactory.create_mock_category()
        product = Product.objects.create(
            kodas='CURRENCY001',
            pavadinimas='Currency Test Product',
            category=category,
            last_purchase_price=Decimal('100.00'),
            currency='EUR'
        )
        
        # For now, just test that the product was created successfully
        self.assertEqual(product.currency, 'EUR')
        self.assertEqual(product.last_purchase_price, Decimal('100.00'))
        
        # In the future, you could add actual currency conversion logic
        # and test it with proper mocking
    
    @patch('django.core.mail.send_mail')
    def test_supplier_notification_mock(self, mock_send_mail):
        """Test supplier notification with mocked email service"""
        mock_send_mail.return_value = True
        
        supplier = MockDataFactory.create_mock_supplier()
        
        # Simulate sending notification
        # In a real application, you might have a method like:
        # supplier.send_notification("Test message")
        
        # For demonstration, we'll just call the mock
        from django.core.mail import send_mail
        send_mail(
            'Test Subject',
            'Test Message',
            'from@test.com',
            [supplier.email],
            fail_silently=False
        )
        
        mock_send_mail.assert_called_once_with(
            'Test Subject',
            'Test Message',
            'from@test.com',
            [supplier.email],
            fail_silently=False
        )


class PerformanceTestCase(TestCase):
    """Performance and optimization test cases"""
    
    def test_category_descendants_performance(self):
        """Test performance of get_descendants with deep hierarchy"""
        # Create deep category hierarchy (10 levels)
        current_category = MockDataFactory.create_mock_category(
            category_code='ROOT',
            name='Root Category'
        )
        
        categories = [current_category]
        for i in range(9):
            current_category = MockDataFactory.create_mock_category(
                parent=current_category,
                category_code=f'LEVEL{i+1}',
                name=f'Level {i+1} Category'
            )
            categories.append(current_category)
        
        # Test that get_descendants works with deep hierarchy
        root = categories[0]
        descendants = root.get_descendants()
        self.assertEqual(len(descendants), 9)  # All except root
        
        # Test that deepest category has correct level
        deepest = categories[-1]
        self.assertEqual(deepest.level, 9)
    
    def test_product_query_optimization(self):
        """Test optimized queries for products with relationships"""
        # Create test data
        categories = [MockDataFactory.create_mock_category() for _ in range(3)]
        suppliers = [MockDataFactory.create_mock_supplier() for _ in range(5)]
        
        products = []
        for i in range(50):
            product = MockDataFactory.create_mock_product(
                category=random.choice(categories),
                suppliers=random.sample(suppliers, k=random.randint(1, 3))
            )
            products.append(product)
        
        # Test efficient querying with select_related and prefetch_related
        with self.assertNumQueries(2):  # Should be optimized to minimal queries
            products_with_relations = Product.objects.select_related('category').prefetch_related('suppliers').all()
            
            # Access related objects (this should not trigger additional queries)
            for product in products_with_relations:
                _ = product.category.name if product.category else None
                _ = list(product.suppliers.all())


class EdgeCaseTestCase(TestCase):
    """Test cases for edge cases and boundary conditions"""
    
    def test_empty_string_vs_null_handling(self):
        """Test handling of empty strings vs null values"""
        category = MockDataFactory.create_mock_category()
        
        # Product with empty string kodas
        product_empty = Product.objects.create(
            kodas='',  # Empty string
            pavadinimas='Empty Code Product',
            category=category
        )
        
        # Product with null kodas
        product_null = Product.objects.create(
            kodas=None,  # Null
            pavadinimas='Null Code Product',
            category=category
        )
        
        # Both should be allowed (unique constraint only applies to non-empty)
        self.assertEqual(product_empty.kodas, '')
        self.assertIsNone(product_null.kodas)
        
        # Test string representation
        self.assertEqual(str(product_empty), ' - Empty Code Product')
        self.assertEqual(str(product_null), 'None - Null Code Product')
    
    def test_category_deletion_cascade_effects(self):
        """Test various cascade effects when deleting categories"""
        # Create hierarchy: Root -> Child -> Grandchild
        root = MockDataFactory.create_mock_category(
            category_code='ROOT',
            name='Root Category'
        )
        child = MockDataFactory.create_mock_category(
            parent=root,
            category_code='CHILD',
            name='Child Category'
        )
        grandchild = MockDataFactory.create_mock_category(
            parent=child,
            category_code='GRANDCHILD',
            name='Grandchild Category'
        )
        
        # Create products in each category
        root_product = MockDataFactory.create_mock_product(category=root)
        child_product = MockDataFactory.create_mock_product(category=child)
        grandchild_product = MockDataFactory.create_mock_product(category=grandchild)
        
        # Delete child category
        child_id = child.id
        child.delete()
        
        # Grandchild should be deleted (CASCADE)
        self.assertFalse(Category.objects.filter(id=child_id).exists())
        self.assertFalse(Category.objects.filter(id=grandchild.id).exists())
        
        # Products should still exist but with null category (SET_NULL)
        child_product.refresh_from_db()
        grandchild_product.refresh_from_db()
        self.assertIsNone(child_product.category)
        self.assertIsNone(grandchild_product.category)
        
        # Root and its product should be unaffected
        self.assertTrue(Category.objects.filter(id=root.id).exists())
        root_product.refresh_from_db()
        self.assertEqual(root_product.category, root)
    
    def test_supplier_product_relationship_edge_cases(self):
        """Test edge cases in supplier-product relationships"""
        supplier = MockDataFactory.create_mock_supplier()
        category = MockDataFactory.create_mock_category()
        
        # Product with no suppliers
        product_no_suppliers = MockDataFactory.create_mock_product(
            category=category,
            suppliers=None
        )
        self.assertEqual(product_no_suppliers.suppliers.count(), 0)
        
        # Add and remove suppliers
        product_no_suppliers.suppliers.add(supplier)
        self.assertEqual(product_no_suppliers.suppliers.count(), 1)
        
        product_no_suppliers.suppliers.remove(supplier)
        self.assertEqual(product_no_suppliers.suppliers.count(), 0)
        
        # Clear all suppliers
        product_with_suppliers = MockDataFactory.create_mock_product(
            category=category,
            suppliers=[supplier]
        )
        product_with_suppliers.suppliers.clear()
        self.assertEqual(product_with_suppliers.suppliers.count(), 0)


# Fixture data for testing
class TestDataFixtures:
    """Pre-defined test data fixtures"""
    
    SAMPLE_CATEGORIES = [
        {'category_code': 'ELEC', 'name': 'Electronics', 'description': 'Electronic devices and components'},
        {'category_code': 'FURN', 'name': 'Furniture', 'description': 'Office and home furniture'},
        {'category_code': 'STAT', 'name': 'Stationery', 'description': 'Office stationery and supplies'},
    ]
    
    SAMPLE_SUPPLIERS = [
        {'company_name': 'TechCorp Solutions', 'email': 'orders@techcorp.com'},
        {'company_name': 'Global Electronics', 'email': 'sales@globalelec.com'},
        {'company_name': 'Office Supplies Inc', 'email': 'info@officesupplies.com'},
        {'company_name': 'Local Distributor', 'email': None},
    ]
    
    SAMPLE_PRODUCTS = [
        {'kodas': 'LAP001', 'pavadinimas': 'Business Laptop', 'price': '1299.99', 'currency': 'USD'},
        {'kodas': 'MOU001', 'pavadinimas': 'Wireless Mouse', 'price': '29.99', 'currency': 'USD'},
        {'kodas': 'CHR001', 'pavadinimas': 'Office Chair', 'price': '299.50', 'currency': 'EUR'},
        {'kodas': 'PEN001', 'pavadinimas': 'Ballpoint Pen Set', 'price': '15.99', 'currency': 'USD'},
    ]
    
    @classmethod
    def create_sample_data(cls):
        """Create sample data for testing"""
        # Create categories
        categories = {}
        for cat_data in cls.SAMPLE_CATEGORIES:
            categories[cat_data['category_code']] = Category.objects.create(**cat_data)
        
        # Create suppliers
        suppliers = []
        for sup_data in cls.SAMPLE_SUPPLIERS:
            suppliers.append(Supplier.objects.create(**sup_data))
        
        # Create products
        products = []
        for i, prod_data in enumerate(cls.SAMPLE_PRODUCTS):
            category = list(categories.values())[i % len(categories)]
            product = Product.objects.create(
                kodas=prod_data['kodas'],
                pavadinimas=prod_data['pavadinimas'],
                category=category,
                last_purchase_price=Decimal(prod_data['price']),
                currency=prod_data['currency']
            )
            # Assign random suppliers
            product.suppliers.add(*random.sample(suppliers, k=random.randint(1, 2)))
            products.append(product)
        
        return categories, suppliers, products


class FixtureTestCase(TestCase):
    """Test cases using predefined fixtures"""
    
    def setUp(self):
        """Set up fixture data"""
        self.categories, self.suppliers, self.products = TestDataFixtures.create_sample_data()
    
    def test_fixture_data_integrity(self):
        """Test that fixture data is created correctly"""
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Supplier.objects.count(), 4)
        self.assertEqual(Product.objects.count(), 4)
        
        # Test relationships
        for product in self.products:
            self.assertIsNotNone(product.category)
            self.assertGreaterEqual(product.suppliers.count(), 1)
    
    def test_fixture_based_queries(self):
        """Test queries using fixture data"""
        # Test products by category
        electronics_products = Product.objects.filter(category__category_code='ELEC')
        self.assertGreater(electronics_products.count(), 0)
        
        # Test products by supplier - ensure we have relationships
        suppliers_with_products = Supplier.objects.filter(products__isnull=False).distinct()
        self.assertGreater(suppliers_with_products.count(), 0)
        
        first_supplier_with_products = suppliers_with_products.first()
        supplier_products = first_supplier_with_products.products.all()
        self.assertGreater(supplier_products.count(), 0)
        
        # Test price filtering
        expensive_products = Product.objects.filter(last_purchase_price__gt=100)
        cheap_products = Product.objects.filter(last_purchase_price__lte=100)
        
        total_products = expensive_products.count() + cheap_products.count()
        self.assertEqual(total_products, Product.objects.count())
