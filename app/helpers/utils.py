from decimal import Decimal
from typing import Optional
from django.db.models import QuerySet, Avg, Model
import openpyxl


def get_average_potential_sales(daily_metrics: QuerySet, min_stock: int) -> float:
    """
    Calculate average potential sales from a QuerySet of daily metrics
    """
    good_stock_metrics: QuerySet = daily_metrics.filter(
        stock__gte=min_stock,
        sales_quantity__isnull=False  # exclude missing data
    )
    
    if good_stock_metrics.exists():
        avg_sales: Optional[Decimal] = good_stock_metrics.aggregate(avg=Avg('sales_quantity'))['avg']
        return float(avg_sales) if avg_sales else 0.0
    else:
        return 0.0


def queryset_to_excel(title: str, headers: list, queryset: QuerySet, row_func=None) -> openpyxl.Workbook:
    wb: openpyxl.Workbook = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for obj in queryset:
        if row_func:
            row = row_func(obj)
        else:
            row = [str(getattr(obj, h, '-')) for h in headers]
        ws.append(row)
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                cell_str = str(cell.value)
                if len(cell_str) > max_length:
                    max_length = len(cell_str)
            except (TypeError, ValueError):
                cell.value = '#N/A'
        ws.column_dimensions[column].width = max_length + 2
    return wb

def product_row(obj):
    suppliers = ', '.join([s.company_name for s in obj.suppliers.all()]) if hasattr(obj, 'suppliers') else '-'
    category = str(getattr(obj, 'category', '')) if getattr(obj, 'category', None) else '-'
    return [
        obj.code,
        obj.model,
        obj.name,
        category,
        suppliers,
        getattr(obj, 'current_stock', None) or 0,
        getattr(obj, 'avg_daily_demand', None) or 0,
        getattr(obj, 'remainder_days', None) or 0,
        getattr(obj, 'po_quantity', None) or 0
    ]

def get_filter_dropdown_queryset(queryset: QuerySet, model: Model, related_name: str) -> list:
    """
    Return distinct model PKs for related name filter dropdowns
    """
    filter_kwargs = {f"{related_name}__in": queryset}
    pk_name = model._meta.pk.name
    return list(model.objects.filter(**filter_kwargs).distinct().values_list(pk_name, flat=True))
