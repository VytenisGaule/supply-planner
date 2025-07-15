from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import QuerySet
from app.models import Product


@csrf_protect
def product_list(request):
    context: dict = {}
    products: QuerySet = Product.objects.all()
    context['products'] = products
    return render(request, 'lists/product_list.html', context=context)