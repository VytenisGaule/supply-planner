from django.core.paginator import Paginator
from django.db.models import QuerySet, Q
from django.db import models
from django.http import QueryDict
from app.models import Product
from app.forms import ItemsPerPageForm, ProductCodeFilterForm, ProductNameFilterForm, ProductCategoryFilterForm, ProductSupplierFilterForm


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
        # Handle both "No category" ('empty') and specific categories
        if 'empty' in category_filter:
            # If "No category" is selected, include products with no category
            category_ids = [cat_id for cat_id in category_filter if cat_id != 'empty']
            if category_ids:
                # Both "No category" and specific categories selected
                products = products.filter(
                    Q(category__isnull=True) | 
                    Q(category__id__in=category_ids)
                )
            else:
                # Only "No category" selected
                products = products.filter(category__isnull=True)
        else:
            # Only specific categories selected
            products = products.filter(category__id__in=category_filter)
    
    if supplier_filter:
        # Handle both "No suppliers" ('empty') and specific suppliers
        if 'empty' in supplier_filter:
            # If "No suppliers" is selected, include products with no suppliers
            supplier_ids = [sup_id for sup_id in supplier_filter if sup_id != 'empty']
            if supplier_ids:
                # Both "No suppliers" and specific suppliers selected
                products = products.filter(
                    Q(suppliers__isnull=True) | 
                    Q(suppliers__id__in=supplier_ids)
                ).distinct()
            else:
                # Only "No suppliers" selected
                products = products.filter(suppliers__isnull=True)
        else:
            # Only specific suppliers selected
            products = products.filter(suppliers__id__in=supplier_filter).distinct()
    
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


