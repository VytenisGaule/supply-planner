from datetime import date
from decimal import Decimal
from typing import Optional
from django.db.models import QuerySet, Avg


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
