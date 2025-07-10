from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.http import HttpResponse

@csrf_protect
def homepage(request):
    context: dict = {}
    return render(request, 'pages/index.html', context=context)
