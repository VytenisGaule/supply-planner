from django.core.paginator import Paginator
from django.db.models import QuerySet, Q
from django.db import models
from django.http import QueryDict
from app.models import Product
from app.forms import ItemsPerPageForm, ProductCodeFilterForm, ProductNameFilterForm, ProductCategoryFilterForm, ProductSupplierFilterForm


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
    products: QuerySet = Product.objects.select_related('category').prefetch_related('suppliers').all()
    
    # Apply filters to the queryset
    if code_filter:
        products = products.filter(kodas__icontains=code_filter)
    
    if name_filter:
        products = products.filter(pavadinimas__icontains=name_filter)
    
    if category_filter:
        products = apply_relation_filter(products, category_filter, 'category')
    
    if supplier_filter:
        products = apply_relation_filter(products, supplier_filter, 'suppliers')
    
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


