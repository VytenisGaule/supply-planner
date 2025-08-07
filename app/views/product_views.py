from django.http import HttpResponse, QueryDict
from django.db.models import QuerySet
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.shortcuts import render
from app.helpers.context import populate_product_list_context, get_product_queryset
from app.helpers.utils import queryset_to_excel

@csrf_protect
def product_list(request):
    context = {}
    populate_product_list_context(request, context)
    return render(request, 'lists/product_list.html', context=context)

@csrf_protect
@require_POST
def get_items_per_page(request):
    """
    get items per page
    """
    context: dict = {}
    items_per_page: str = request.POST.get('items_per_page', '20')
    request.session['items_per_page'] = int(items_per_page)
    populate_product_list_context(request, context)
    return render(request, 'lists/product_list.html', context=context)

@csrf_protect
@require_POST
def get_order_days(request):
    """
    get order days
    """
    context: dict = {}
    request.session['order_days_data'] = request.POST
    populate_product_list_context(request, context)
    return render(request, 'lists/product_list.html', context=context)

@csrf_protect
@require_POST
def get_product_filter(request):
    """
    get product filter
    """
    context: dict = {}
    request.session['filter_data'] = request.POST
    populate_product_list_context(request, context)
    return render(request, 'lists/product_list.html', context=context)

def export_product_list_to_excel(request):
    filter_data: QueryDict = request.session.get('filter_data', QueryDict())
    order_days_data: QueryDict = request.session.get('order_days_data', QueryDict())
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
    order_days_value = order_days_data.get('order_days', '') or 0
        
    products: QuerySet = get_product_queryset(
        order_days_value=order_days_value,
        code_filter=code_filter,
        name_filter=name_filter,
        category_filter=category_filter,
        supplier_filter=supplier_filter,
        min_stock=min_stock,
        max_stock=max_stock,
        min_daily_demand=min_daily_demand,
        max_daily_demand=max_daily_demand,
        min_remainder_days=min_remainder_days,
        max_remainder_days=max_remainder_days,
        min_po_quantity=min_po_quantity,
        max_po_quantity=max_po_quantity
    )

    headers = [
        'Code', 'Name', 'Category', 'Suppliers', 'Current stock', 'Daily Demand', 'Days Left', 'PO Qty'
    ]
    wb = queryset_to_excel('Products', headers, products)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=products.xlsx'
    wb.save(response)
    return response