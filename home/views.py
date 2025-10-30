from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *


def home_view(request):
    items = Item.objects.all()
    context = {'items': items}
    return render(request, 'home.html', context)


def create_item_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        item = Item.objects.create(name=name)
        return HttpResponse(f'<li class="text-8xl font-thin">{item.name}</li>')
    else:
        return redirect('home')