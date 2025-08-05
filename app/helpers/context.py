from django.core.paginator import Paginator
from django.db.models import QuerySet, Q, Avg, Subquery, OuterRef, IntegerField, FloatField, Case, When, F
from django.db.models.functions import Round, Greatest
from django.http import QueryDict
from app.models import Product, DailyMetrics
from app.forms import ItemsPerPageForm, ProductCodeFilterForm, ProductNameFilterForm, ProductCategoryFilterForm, ProductSupplierFilterForm, ProductStockFilterForm, ProductDailyDemandFilterForm, ProductRemainderDaysFilterForm, OrderDaysForm, ProductPOQuantityFilterForm
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


def apply_min_max_filter(queryset: QuerySet, field_name: str, min_value: str, max_value: str, value_type: type = int) -> QuerySet:
    """    Apply min/max filtering to a queryset field with proper None handling    """
    # Apply min filter
    if min_value:
        try:
            min_val = value_type(min_value)
            # Only include products with valid values >= min (exclude None)
            queryset = queryset.filter(**{f'{field_name}__gte': min_val})
        except ValueError:
            pass  # Invalid input, ignore filter
    
    # Apply max filter
    if max_value:
        try:
            max_val = value_type(max_value)
            # Only include products with valid values <= max (exclude None)
            queryset = queryset.filter(Q(**{f'{field_name}__lte': max_val}) | Q(**{f'{field_name}__isnull': True}))
        except ValueError:
            pass  # Invalid input, ignore filter
    
    return queryset


def populate_product_list_context(request, context):
    """
    Context filler for product list data with pagination
    """
    items_per_page: int = request.session.get('items_per_page', 20)
    filter_data: QueryDict = request.session.get('filter_data', QueryDict())
    order_days_data: QueryDict = request.session.get('order_days_data', QueryDict())

    items_per_page_form: ItemsPerPageForm = ItemsPerPageForm(initial={'items_per_page': items_per_page})
    order_days_form: OrderDaysForm = OrderDaysForm(data=order_days_data)
    code_filter_form: ProductCodeFilterForm = ProductCodeFilterForm(data=filter_data)
    name_filter_form: ProductNameFilterForm = ProductNameFilterForm(data=filter_data)
    category_filter_form: ProductCategoryFilterForm = ProductCategoryFilterForm(data=filter_data)
    supplier_filter_form: ProductSupplierFilterForm = ProductSupplierFilterForm(data=filter_data)
    stock_filter_form: ProductStockFilterForm = ProductStockFilterForm(data=filter_data)
    daily_demand_filter_form: ProductDailyDemandFilterForm = ProductDailyDemandFilterForm(data=filter_data)
    remainder_days_filter_form: ProductRemainderDaysFilterForm = ProductRemainderDaysFilterForm(data=filter_data)
    product_po_quantity_filter_form: ProductPOQuantityFilterForm = ProductPOQuantityFilterForm(data=filter_data)
    order_days_form.is_valid()
    code_filter_form.is_valid()
    name_filter_form.is_valid()
    category_filter_form.is_valid()
    supplier_filter_form.is_valid()
    stock_filter_form.is_valid()
    daily_demand_filter_form.is_valid()
    remainder_days_filter_form.is_valid()
    product_po_quantity_filter_form.is_valid()
    
    code_filter: str = filter_data.get('code', '')
    name_filter: str = filter_data.get('name', '')
    category_filter: list = filter_data.getlist('categories') if hasattr(filter_data, 'getlist') else filter_data.get('categories', [])
    supplier_filter: list = filter_data.getlist('suppliers') if hasattr(filter_data, 'getlist') else filter_data.get('suppliers', [])
    min_stock: str = filter_data.get('min_stock', '')
    max_stock: str = filter_data.get('max_stock', '')
    min_daily_demand: str = filter_data.get('min_daily_demand', '')
    max_daily_demand: str = filter_data.get('max_daily_demand', '')
    min_remainder_days: str = filter_data.get('min_remainder_days', '')
    max_remainder_days: str = filter_data.get('max_remainder_days', '')
    min_po_quantity: str = filter_data.get('min_po_quantity', '')
    max_po_quantity: str = filter_data.get('max_po_quantity', '')

    # Calculate date range for average daily demand (365 days back)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    # Get order_days value from form (default 1)
    order_days_value: int = 0
    if order_days_form.is_valid():
        try:
            order_days_value: int = int(order_days_form.cleaned_data.get('order_days', 0))
        except (ValueError, TypeError):
            pass
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
        ),
        # PO quantity: avg_daily_demand * max(order_days_value - current_stock_coverage, 0)
        po_quantity=Case(
            When(
                Q(avg_daily_demand__isnull=False) & Q(avg_daily_demand__gt=0) & Q(current_stock__isnull=False),
                then=Round(F('avg_daily_demand') * Greatest(order_days_value - (F('current_stock') / F('avg_daily_demand')), 0, output_field=FloatField()), output_field=FloatField())
            ),
            default=0,
            output_field=IntegerField()
        )
    ).filter(is_active=True).order_by('code')

    # Apply filters to the queryset
    if code_filter:
        products = products.filter(code__icontains=code_filter)
    
    if name_filter:
        products = products.filter(name__icontains=name_filter)
    
    if category_filter:
        products = apply_relation_filter(products, category_filter, 'category')
    
    if supplier_filter:
        products = apply_relation_filter(products, supplier_filter, 'suppliers')

    if min_stock or max_stock:
        products = apply_min_max_filter(products, 'current_stock', min_stock, max_stock, int)
    
    if min_daily_demand or max_daily_demand:
        products = apply_min_max_filter(products, 'avg_daily_demand', min_daily_demand, max_daily_demand, float)

    if min_remainder_days or max_remainder_days:
        products = apply_min_max_filter(products, 'remainder_days', min_remainder_days, max_remainder_days, int)
        
    if min_po_quantity or max_po_quantity:
        products = apply_min_max_filter(products, 'po_quantity', min_po_quantity, max_po_quantity, int)

    # Pagination
    paginator: Paginator = Paginator(products, items_per_page)
    page_number: str = request.GET.get('page') if request.GET.get('page') else request.POST.get('page_number', 1)
    page_obj = paginator.get_page(page_number)
    
    # Update the context dictionary
    context['products'] = page_obj
    context['paginator'] = paginator
    context['items_per_page'] = items_per_page
    context['order_days_form'] = order_days_form
    context['items_per_page_form'] = items_per_page_form
    context['code_filter_form'] = code_filter_form
    context['name_filter_form'] = name_filter_form
    context['category_filter_form'] = category_filter_form
    context['supplier_filter_form'] = supplier_filter_form
    context['stock_filter_form'] = stock_filter_form
    context['daily_demand_filter_form'] = daily_demand_filter_form
    context['remainder_days_filter_form'] = remainder_days_filter_form
    context['product_po_quantity_filter_form'] = product_po_quantity_filter_form
    context['selected_categories'] = category_filter
    context['selected_suppliers'] = supplier_filter

