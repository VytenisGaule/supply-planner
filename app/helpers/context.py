from django.core.paginator import Paginator
from django.db.models import QuerySet, Q, Avg, Subquery, OuterRef, IntegerField, FloatField, Case, When, F
from django.http import QueryDict
from app.models import Product, DailyMetrics
from app.forms import ItemsPerPageForm, ProductCodeFilterForm, ProductNameFilterForm, ProductCategoryFilterForm, ProductSupplierFilterForm
from datetime import datetime, timedelta


def apply_relation_filter(queryset: QuerySet, filter_list: list, field_name: str) -> QuerySet:
    """ Apply filtering   """
    if not filter_list:
        return queryset
    if 'empty' in filter_list:
        specific_ids = [item_id for item_id in filter_list if item_id != 'empty']
        if specific_ids:
            filtered_queryset = queryset.filter(
                Q(**{f'{field_name}__isnull': True}) | 
                Q(**{f'{field_name}__id__in': specific_ids})
            )
        else:
            filtered_queryset = queryset.filter(**{f'{field_name}__isnull': True})
    else:
        filtered_queryset = queryset.filter(**{f'{field_name}__id__in': filter_list})
    return filtered_queryset.distinct()


def populate_product_list_context(request, context):
    """
    Context filler for product list data with pagination
    """
    filter_data: QueryDict = request.session.get('filter_data', QueryDict())
    code_filter: str = filter_data.get('code', '')
    name_filter: str = filter_data.get('name', '')
    category_filter: list = filter_data.getlist('categories') if hasattr(filter_data, 'getlist') else filter_data.get('categories', [])
    supplier_filter: list = filter_data.getlist('suppliers') if hasattr(filter_data, 'getlist') else filter_data.get('suppliers', [])
    
    # Min/max filters
    min_stock: str = filter_data.get('min_stock', '')
    max_stock: str = filter_data.get('max_stock', '')
    min_daily_demand: str = filter_data.get('min_daily_demand', '')
    max_daily_demand: str = filter_data.get('max_daily_demand', '')
    min_remainder_days: str = filter_data.get('min_remainder_days', '')
    max_remainder_days: str = filter_data.get('max_remainder_days', '')
    
    # Calculate date range for average daily demand (365 days back)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    # Annotate products with calculated fields
    products: QuerySet = Product.objects.select_related('category').prefetch_related('suppliers').annotate(
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
            default=None,  # Return None for N/A cases instead of 999
            output_field=IntegerField()
        )
    ).all()
    
    # Apply filters to the queryset
    if code_filter:
        products = products.filter(kodas__icontains=code_filter)
    
    if name_filter:
        products = products.filter(pavadinimas__icontains=name_filter)
    
    if category_filter:
        products = apply_relation_filter(products, category_filter, 'category')
    
    if supplier_filter:
        products = apply_relation_filter(products, supplier_filter, 'suppliers')
    
    # Apply min/max filters on annotated fields
    if min_stock:
        try:
            min_stock_val = int(min_stock)
            # Only include products with valid stock >= min (exclude None)
            products = products.filter(current_stock__gte=min_stock_val)
        except ValueError:
            pass  # Invalid input, ignore filter
    
    if max_stock:
        try:
            max_stock_val = int(max_stock)
            # Include products with stock <= max OR None (N/A)
            products = products.filter(
                Q(current_stock__lte=max_stock_val) | 
                Q(current_stock__isnull=True)
            )
        except ValueError:
            pass  # Invalid input, ignore filter
    
    if min_daily_demand:
        try:
            min_daily_demand_val = float(min_daily_demand)
            # When min is specified, only include products with valid values >= min
            # Exclude NULL/N/A products
            products = products.filter(avg_daily_demand__gte=min_daily_demand_val)
        except ValueError:
            pass  # Invalid input, ignore filter
    
    if max_daily_demand:
        try:
            max_daily_demand_val = float(max_daily_demand)
            # When max is specified, include products <= max OR NULL/N/A
            products = products.filter(
                Q(avg_daily_demand__lte=max_daily_demand_val) | 
                Q(avg_daily_demand__isnull=True)
            )
        except ValueError:
            pass  # Invalid input, ignore filter
    
    if min_remainder_days:
        try:
            min_remainder_days_val = int(min_remainder_days)
            # When min is specified, only include products with valid values >= min
            # Exclude None/N/A products
            products = products.filter(remainder_days__gte=min_remainder_days_val)
        except ValueError:
            pass  # Invalid input, ignore filter
    
    if max_remainder_days:
        try:
            max_remainder_days_val = int(max_remainder_days)
            # When max is specified, include products <= max OR None/N/A cases
            products = products.filter(
                Q(remainder_days__lte=max_remainder_days_val) |
                Q(remainder_days__isnull=True)  # Include N/A cases
            )
        except ValueError:
            pass  # Invalid input, ignore filter
    
    items_per_page: int = request.session.get('items_per_page', 20)
    
    items_per_page_form: ItemsPerPageForm = ItemsPerPageForm(initial={'items_per_page': items_per_page})
    code_filter_form: ProductCodeFilterForm = ProductCodeFilterForm(data=filter_data)
    name_filter_form: ProductNameFilterForm = ProductNameFilterForm(data=filter_data)
    category_filter_form: ProductCategoryFilterForm = ProductCategoryFilterForm(data=filter_data)
    supplier_filter_form: ProductSupplierFilterForm = ProductSupplierFilterForm(data=filter_data)
    code_filter_form.is_valid()
    name_filter_form.is_valid()
    category_filter_form.is_valid()
    supplier_filter_form.is_valid()

    # Pagination
    paginator: Paginator = Paginator(products, items_per_page)
    page_number: str = request.GET.get('page') if request.GET.get('page') else request.POST.get('page_number', 1)
    page_obj = paginator.get_page(page_number)
    
    # Update the context dictionary
    context['products'] = page_obj
    context['paginator'] = paginator
    context['items_per_page'] = items_per_page
    context['items_per_page_form'] = items_per_page_form
    context['code_filter_form'] = code_filter_form
    context['name_filter_form'] = name_filter_form
    context['category_filter_form'] = category_filter_form
    context['supplier_filter_form'] = supplier_filter_form
    
    # Add selected values for JavaScript
    context['selected_categories'] = category_filter
    context['selected_suppliers'] = supplier_filter


