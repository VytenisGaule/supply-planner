from django import forms


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
