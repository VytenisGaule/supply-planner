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
    
    categories = forms.MultipleChoiceField(
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add "No category" option first, then all categories
        choices = [('empty', 'Be kategorijos')]
        choices.extend([(cat.id, cat.name) for cat in Category.objects.all()])
        self.fields['categories'].choices = choices


class ProductSupplierFilterForm(forms.Form):
    """Form for filtering products by suppliers with custom multi-select"""
    
    suppliers = forms.MultipleChoiceField(
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add "No suppliers" option first, then all suppliers
        choices = [('empty', 'Be tiekėjų')]
        choices.extend([(sup.id, sup.company_name) for sup in Supplier.objects.all()])
        self.fields['suppliers'].choices = choices


class MinMaxFilterForm(forms.Form):
    """Base form for min/max filtering with reusable fields"""
    
    def __init__(self, field_name, placeholder_prefix, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields[f'min_{field_name}'] = forms.CharField(
            required=False,
            max_length=10,
            widget=forms.TextInput(attrs={
                'name': f'min_{field_name}',
                'x-model': f'filters.min_{field_name}',
                'placeholder': f'Min {placeholder_prefix}',
                'class': 'filter-input text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            })
        )
        
        self.fields[f'max_{field_name}'] = forms.CharField(
            required=False,
            max_length=10,
            widget=forms.TextInput(attrs={
                'name': f'max_{field_name}',
                'x-model': f'filters.max_{field_name}',
                'placeholder': f'Max {placeholder_prefix}',
                'class': 'filter-input text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            })
        )

    def clean(self):
        cleaned_data = super().clean()
        for key in list(cleaned_data):
            value = cleaned_data[key]
            if value is not None and value != '':
                try:
                    float(value)
                except ValueError:
                    self.add_error(key, 'Enter a valid number.')
        return cleaned_data


class ProductStockFilterForm(MinMaxFilterForm):
    """Form for filtering products by current stock (min/max)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__('stock', 'stock', *args, **kwargs)


class ProductDailyDemandFilterForm(MinMaxFilterForm):
    """Form for filtering products by average daily demand (min/max)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__('daily_demand', 'demand', *args, **kwargs)


class ProductRemainderDaysFilterForm(MinMaxFilterForm):
    """Form for filtering products by remainder days (min/max)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__('remainder_days', 'days', *args, **kwargs)
