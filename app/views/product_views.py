from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.shortcuts import render
from app.helpers.context import populate_product_list_context

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
def get_product_filter(request):
    """
    get product filter
    """
    context: dict = {}
    request.session['filter_data'] = request.POST
    populate_product_list_context(request, context)
    return render(request, 'lists/product_list.html', context=context)