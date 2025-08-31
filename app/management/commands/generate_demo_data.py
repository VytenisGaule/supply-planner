from django.core.management.base import BaseCommand
from app.models import Supplier, Category, Product, DailyMetrics
from django.db import transaction
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Generate demo data: 200 categories, 200 suppliers, 10k products, 2 years of daily metrics.'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Deleting existing data...')
            DailyMetrics.objects.all().delete()
            Product.objects.all().delete()
            Supplier.objects.all().delete()
            Category.objects.all().delete()

            self.stdout.write('Creating categories...')
            categories = []
            for i in range(200):
                parent = random.choice(categories) if categories and random.random() < 0.5 else None
                cat = Category.objects.create(
                    category_code=f'C{i:03d}',
                    name=f'Category {i+1}',
                    description=f'Description for category {i+1}',
                    parent=parent
                )
                categories.append(cat)

            self.stdout.write('Creating suppliers...')
            suppliers = []
            for i in range(200):
                sup = Supplier.objects.create(
                    company_name=f'Supplier {i+1}',
                    email=f'supplier{i+1}@example.com'
                )
                suppliers.append(sup)

            self.stdout.write('Creating products...')
            products = []
            for i in range(10000):
                cat = random.choice(categories)
                prod = Product.objects.create(
                    code=f'P{i+1:05d}',
                    name=f'Product {i+1}',
                    category=cat,
                    last_purchase_price=random.uniform(1, 1000),
                    currency=random.choice(['USD', 'EUR']),
                    is_internet=random.choice([True, False]),
                    lead_time=random.randint(1, 180),
                    is_active=True,
                    moq=random.randint(1, 20)
                )
                prod.suppliers.set(random.sample(suppliers, random.randint(1, 5)))
                products.append(prod)

            self.stdout.write('Creating daily metrics...')
            start_date = datetime.now().date() - timedelta(days=730)
            for prod in products:
                metrics = []
                stock = random.randint(0, 500)
                for d in range(730):
                    date = start_date + timedelta(days=d)
                    sales = random.randint(0, 20)
                    stock = max(0, stock + random.randint(-10, 10) - sales)
                    metrics.append(DailyMetrics(
                        product=prod,
                        date=date,
                        sales_quantity=sales,
                        stock=stock,
                        potential_sales=sales + random.uniform(0, 5)
                    ))
                DailyMetrics.objects.bulk_create(metrics)

            self.stdout.write(self.style.SUCCESS('Demo data generation complete.'))
