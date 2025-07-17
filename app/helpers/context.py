from django.core.paginator import Paginator
from django.db.models import QuerySet
from app.models import Product
from app.forms import ItemsPerPageForm, ProductCodeFilterForm, ProductNameFilterForm


def populate_product_list_context(request, context):
    """
    Context filler for product list data with pagination
    """
    products: QuerySet = Product.objects.select_related('category').prefetch_related('suppliers').all()
    items_per_page: int = request.session.get('items_per_page', 20)
    filter_data: dict = request.session.get('filter_data', {})
    
    # Create form with current value
    items_per_page_form: ItemsPerPageForm = ItemsPerPageForm(initial={'items_per_page': items_per_page})
    code_filter_form: ProductCodeFilterForm = ProductCodeFilterForm(data=filter_data)
    name_filter_form: ProductNameFilterForm = ProductNameFilterForm(data=filter_data)
    code_filter_form.is_valid()
    name_filter_form.is_valid()

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


