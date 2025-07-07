from datetime import date
from typing import Optional
from app.models import DailyMetrics, Product


def get_last_good_stock_date(product: Product, min_stock: int = 1) -> Optional[date]:
    """
    Find date when product stock above min_stock.
    """
    last_good_stock: DailyMetrics = DailyMetrics.objects.filter(
        product=product,
        stock__gte=min_stock,
    ).order_by('-date').first()
    if not last_good_stock:
        return None
    return last_good_stock.date