from django.core.paginator import Paginator
from django.db.models import QuerySet
from app.models import Product
from app.forms import ItemsPerPageForm


def populate_product_list_context(request, context):
    """
    Context filler for product list data with pagination
    """
    products: QuerySet = Product.objects.select_related('category').prefetch_related('suppliers').all()
    items_per_page: int = request.session.get('items_per_page', 20)
    
    # Create form with current value
    form = ItemsPerPageForm(initial={'items_per_page': items_per_page})
    
    # Pagination
    paginator: Paginator = Paginator(products, items_per_page)
    page_number: str = request.GET.get('page') if request.GET.get('page') else request.POST.get('page_number', 1)
    page_obj = paginator.get_page(page_number)
    
    # Update the context dictionary
    context['products'] = page_obj
    context['paginator'] = paginator
    context['items_per_page'] = items_per_page
    context['items_per_page_form'] = form


