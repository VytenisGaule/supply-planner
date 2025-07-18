from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from app.helpers.context import populate_product_list_context

@csrf_protect
def homepage(request):
    context = {}
    populate_product_list_context(request, context)
    
    return render(request, 'pages/index.html', context=context)
