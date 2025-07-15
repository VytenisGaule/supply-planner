from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.http import HttpResponse
from app.helpers.context import populate_product_list_context

@csrf_protect
def product_list(request):
    context = {}
    populate_product_list_context(request, context)
    return render(request, 'lists/product_list.html', context=context)