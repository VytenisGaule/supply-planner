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
        label="Items per page", 
        widget=forms.Select(attrs={
            'id': 'items-per-page',
            'class': 'border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
class OrderDaysForm(forms.Form):
    """Form for MOQ days input"""
    order_days = forms.IntegerField(
        required=False,
        min_value=1,
        label="Set order days",
        widget=forms.TextInput(attrs={
            'name': 'order_days',
            'placeholder': 'Order days',
            'class': 'filter-input text-sm bg-gray-100 border-2',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        order_days = cleaned_data.get('order_days')
        if order_days is not None and order_days < 1:
            self.add_error('order_days', 'Enter a positive number')
        # Normalize order_days to string integer if valid
        if order_days is not None and order_days != '':
            try:
                self.data = self.data.copy()
                self.data['order_days'] = str(int(float(order_days)))
            except ValueError:
                self.add_error('order_days', 'Enter a positive number')
        return cleaned_data

class ProductCodeFilterForm(forms.Form):
    """Form for filtering products by code"""
    
    code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'name': 'code',
            'placeholder': 'Filter by code...',
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
        })
    )


class ProductModelFilterForm(forms.Form):
    """Form for filtering products by model"""
    
    model = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'name': 'model',
            'placeholder': 'Filter by model...',
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
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            'data-select2': 'true',
            'data-placeholder': 'Select categories...',
            'multiple': 'multiple'
        })
    )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add "No category" option first, then all categories
        category_ids: list[int] = request.session.get('category_ids')
        if category_ids is None:
            category_ids = list(Category.objects.values_list('id', flat=True))
        if Category.objects.filter(id__in=category_ids).filter(products__isnull=True).exists():
            choices: list[tuple] = [('empty', 'Be kategorijos')]
        else:
            choices: list[tuple] = []
        choices.extend([(cat.id, cat.name) for cat in Category.objects.filter(id__in=category_ids)])
        self.fields['categories'].choices = choices


class ProductSupplierFilterForm(forms.Form):
    """Form for filtering products by suppliers with custom multi-select"""
    
    suppliers = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            'name': 'suppliers',
            'class': 'w-full p-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            'data-select2': 'true',
            'data-placeholder': 'Select suppliers...',
            'multiple': 'multiple'
        })
    )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add "No suppliers" option first, then all suppliers
        supplier_ids: list[int] = request.session.get('supplier_ids')
        if supplier_ids is None:
            supplier_ids = list(Supplier.objects.values_list('id', flat=True))
        if Supplier.objects.filter(id__in=supplier_ids).filter(products__isnull=True).exists():
            choices: list[tuple] = [('empty', 'Be tiekėjų')]
        else:
            choices: list[tuple] = []
        choices.extend([(sup.id, sup.company_name) for sup in Supplier.objects.filter(id__in=supplier_ids)])
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
                'placeholder': 'Min',
                'class': 'filter-input text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            })
        )
        
        self.fields[f'max_{field_name}'] = forms.CharField(
            required=False,
            max_length=10,
            widget=forms.TextInput(attrs={
                'name': f'max_{field_name}',
                'placeholder': 'Max',
                'class': 'filter-input text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500',
            })
        )

    def clean(self):
        cleaned_data: dict = super().clean()
        normalized_data: dict = {}
        for key in list(cleaned_data):
            value = cleaned_data[key]
            if value is not None and value != '':
                try:
                    normalized_data[key] = str(int(float(value)))
                except ValueError:
                    self.add_error(key, 'Enter a valid number.')
        self.data = self.data.copy()
        for key, v in normalized_data.items():
            self.data[key] = v
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

class ProductPOQuantityFilterForm(MinMaxFilterForm):
    """Form for filtering products by PO quantity (min/max)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__('po_quantity', 'quantity', *args, **kwargs)