"""
Management command to test and fix supplier relationships
"""

from django.core.management.base import BaseCommand
from app.models import Product, Supplier


class Command(BaseCommand):
    help = 'Test and fix supplier relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-suppliers',
            action='store_true',
            help='Create test suppliers and assign them to products',
        )
        parser.add_argument(
            '--debug-product',
            type=str,
            help='Debug specific product code',
        )
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='List all products and their suppliers',
        )

    def handle(self, *args, **options):
        if options['create_test_suppliers']:
            self.create_test_suppliers()
        
        if options['debug_product']:
            self.debug_specific_product(options['debug_product'])
        
        if options['list_all']:
            self.list_all_products()

    def create_test_suppliers(self):
        """Create test suppliers and assign them to products"""
        
        # Create some test suppliers
        suppliers_data = [
            {'company_name': 'ABC Corporation', 'email': 'contact@abc-corp.com'},
            {'company_name': 'XYZ Limited', 'email': 'sales@xyz-ltd.com'},
            {'company_name': 'Global Supplies Inc', 'email': 'orders@globalsupplies.com'},
            {'company_name': 'Best Products Ltd', 'email': 'info@bestproducts.com'},
        ]
        
        suppliers = []
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                company_name=supplier_data['company_name'],
                defaults={'email': supplier_data['email']}
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f"✅ Created supplier: {supplier.company_name}")
            else:
                self.stdout.write(f"📦 Supplier exists: {supplier.company_name}")
        
        # Assign suppliers to products
        products = Product.objects.all()[:10]  # First 10 products
        
        if not products:
            self.stdout.write(self.style.ERROR("❌ No products found. Create some products first."))
            return
        
        import random
        for product in products:
            # Assign 1-3 random suppliers to each product
            num_suppliers = random.randint(1, 3)
            selected_suppliers = random.sample(suppliers, min(num_suppliers, len(suppliers)))
            
            # Clear existing suppliers first
            product.suppliers.clear()
            
            # Add new suppliers
            for supplier in selected_suppliers:
                product.suppliers.add(supplier)
            
            supplier_names = product.get_supplier_names()
            self.stdout.write(f"🔗 {product.kodas}: {supplier_names}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Assigned suppliers to {len(products)} products"))

    def debug_specific_product(self, product_code):
        """Debug a specific product's supplier relationships"""
        try:
            product = Product.objects.get(kodas=product_code)
            
            self.stdout.write(f"\n🔍 DEBUGGING PRODUCT: {product_code}")
            self.stdout.write("-" * 40)
            
            debug_info = product.debug_suppliers()
            
            self.stdout.write(f"Product ID: {debug_info['product_id']}")
            self.stdout.write(f"Suppliers count: {debug_info['suppliers_count']}")
            self.stdout.write(f"Supplier IDs: {debug_info['supplier_ids']}")
            self.stdout.write(f"Supplier names: {debug_info['supplier_names']}")
            
            # Test the get_supplier_names method
            supplier_names = product.get_supplier_names()
            self.stdout.write(f"get_supplier_names() result: '{supplier_names}'")
            
            # Check through relationships table directly
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT s.company_name 
                    FROM app_supplier s 
                    JOIN app_supplier_products sp ON s.id = sp.supplier_id 
                    WHERE sp.product_id = %s
                """, [product.id])
                direct_suppliers = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"Direct DB query result: {direct_suppliers}")
            
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Product {product_code} not found"))

    def list_all_products(self):
        """List all products and their suppliers"""
        products = Product.objects.all()
        
        if not products:
            self.stdout.write(self.style.ERROR("❌ No products found"))
            return
        
        self.stdout.write(f"\n📋 ALL PRODUCTS AND SUPPLIERS:")
        self.stdout.write("=" * 60)
        
        for product in products:
            suppliers = product.suppliers.all()
            supplier_count = suppliers.count()
            supplier_names = product.get_supplier_names()
            
            self.stdout.write(f"{product.kodas:<15} | {supplier_count} suppliers | {supplier_names}")
        
        # Summary
        total_products = products.count()
        products_with_suppliers = products.filter(suppliers__isnull=False).distinct().count()
        products_without_suppliers = total_products - products_with_suppliers
        
        self.stdout.write("\n📊 SUMMARY:")
        self.stdout.write(f"Total products: {total_products}")
        self.stdout.write(f"With suppliers: {products_with_suppliers}")
        self.stdout.write(f"Without suppliers: {products_without_suppliers}")
