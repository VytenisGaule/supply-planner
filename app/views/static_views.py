from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import QuerySet
from django.core.paginator import Paginator
from app.models import Product

@csrf_protect
def homepage(request):
    context: dict = {}
    products: QuerySet = Product.objects.select_related('category').prefetch_related('suppliers').all()
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context['products'] = page_obj
    context['paginator'] = paginator
    return render(request, 'pages/index.html', context=context)
