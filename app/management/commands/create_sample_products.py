from django.core.management.base import BaseCommand
from app.models import Product, Category, Supplier
import random

class Command(BaseCommand):
    help = 'Create 20 sample products with categories and suppliers'

    def handle(self, *args, **options):
        # Create sample categories
        categories_data = [
            'Electronics',
            'Office Supplies',
            'Furniture',
            'Clothing',
            'Kitchen',
            'Tools',
            'Books',
            'Sports',
            'Health',
            'Automotive'
        ]
        
        categories = []
        for i, cat_name in enumerate(categories_data):
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={
                    'category_code': f'CAT{i+1:03d}',
                    'description': f'Category for {cat_name} products'
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {cat_name}')

        # Create sample suppliers
        suppliers_data = [
            ('Supplier A', 'supplier_a@example.com'),
            ('Supplier B', 'supplier_b@example.com'),
            ('Supplier C', 'supplier_c@example.com'),
            ('Supplier D', 'supplier_d@example.com'),
            ('Supplier E', 'supplier_e@example.com'),
            ('Supplier F', 'supplier_f@example.com'),
            ('Supplier G', 'supplier_g@example.com'),
            ('Supplier H', 'supplier_h@example.com'),
            ('Supplier I', 'supplier_i@example.com'),
            ('Supplier J', 'supplier_j@example.com'),
            ('Supplier K', 'supplier_k@example.com'),
            ('Supplier L', 'supplier_l@example.com'),
        ]
        
        suppliers = []
        for sup_name, email in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                company_name=sup_name,
                defaults={
                    'email': email,
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'Created supplier: {sup_name}')

        # Create 20 sample products
        products_data = [
            ('PRD001', 'Laptop Computer', 'Electronics'),
            ('PRD002', 'Office Chair', 'Furniture'),
            ('PRD003', 'Printer Paper', 'Office Supplies'),
            ('PRD004', 'Business Shirt', 'Clothing'),
            ('PRD005', 'Coffee Machine', 'Kitchen'),
            ('PRD006', 'Screwdriver Set', 'Tools'),
            ('PRD007', 'Programming Book', 'Books'),
            ('PRD008', 'Tennis Racket', 'Sports'),
            ('PRD009', 'First Aid Kit', 'Health'),
            ('PRD010', 'Car Battery', 'Automotive'),
            ('PRD011', 'Smartphone', 'Electronics'),
            ('PRD012', 'Desk Lamp', 'Furniture'),
            ('PRD013', 'Stapler', 'Office Supplies'),
            ('PRD014', 'Casual Pants', 'Clothing'),
            ('PRD015', 'Blender', 'Kitchen'),
            ('PRD016', 'Hammer', 'Tools'),
            ('PRD017', 'Notebook', 'Books'),
            ('PRD018', 'Football', 'Sports'),
            ('PRD019', 'Thermometer', 'Health'),
            ('PRD020', 'Motor Oil', 'Automotive'),
        ]

        for kodas, pavadinimas, category_name in products_data:
            # Find the category
            category = next((c for c in categories if c.name == category_name), None)
            
            # Create or get product
            product, created = Product.objects.get_or_create(
                kodas=kodas,
                defaults={
                    'pavadinimas': pavadinimas,
                    'category': category,
                    'last_purchase_price': round(random.uniform(10, 1000), 2),
                    'lead_time': random.randint(1, 30),
                }
            )
            
            if created:
                # Add random suppliers to the product
                num_suppliers = random.randint(1, 4)  # Each product has 1-4 suppliers
                random_suppliers = random.sample(suppliers, num_suppliers)
                product.suppliers.set(random_suppliers)
                
                self.stdout.write(f'Created product: {kodas} - {pavadinimas}')
            else:
                self.stdout.write(f'Product already exists: {kodas} - {pavadinimas}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created/updated 20 products with categories and suppliers!')
        )
