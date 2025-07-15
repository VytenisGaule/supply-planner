from django.core.paginator import Paginator
from django.db.models import QuerySet
from app.models import Product


def populate_product_list_context(request, context):
    """
    Context filler for product list data with pagination
    """
    products: QuerySet = Product.objects.select_related('category').prefetch_related('suppliers').all()
    items_per_page: int = request.session.get('items_per_page', 20)
    
    # Pagination
    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Update the context dictionary
    context['products'] = page_obj
    context['paginator'] = paginator


