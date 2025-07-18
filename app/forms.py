from django import forms
from app.models import Category, Supplier


class ItemsPerPageForm(forms.Form):
    ITEMS_PER_PAGE_CHOICES = [
        (10, '10'),
        (20, '20'),
        (30, '30'),
        (40, '40'),
        (50, '50'),
    ]
    
    items_per_page = forms.ChoiceField(
        choices=ITEMS_PER_PAGE_CHOICES,
        widget=forms.Select(attrs={
            'id': 'items-per-page',
            'class': 'border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'x-model': 'items_per_page'
        })
    )


class ProductCodeFilterForm(forms.Form):
    """Form for filtering products by code"""
    
    code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'name': 'code',
            'x-model': 'filters.code',
            'placeholder': 'Filter by code...',
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
        })
    )


class ProductNameFilterForm(forms.Form):
    """Form for filtering products by name"""
    
    name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'name': 'name',
            'x-model': 'filters.name',
            'placeholder': 'Filter by name...',
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
        })
    )


class ProductCategoryFilterForm(forms.Form):
    """Form for filtering products by categories with custom multi-select"""
    
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'name': 'categories',
            'x-model': 'filters.categories',
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            'data-select2': 'true',
            'data-placeholder': 'Select categories...',
            'multiple': 'multiple'
        })
    )


class ProductSupplierFilterForm(forms.Form):
    """Form for filtering products by suppliers with custom multi-select"""
    
    suppliers = forms.ModelMultipleChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'name': 'suppliers',
            'x-model': 'filters.suppliers',
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            'data-select2': 'true',
            'data-placeholder': 'Select suppliers...',
            'multiple': 'multiple'
        })
    )
