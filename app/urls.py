from django.urls import include, path
from rest_framework import routers
from app.views.static_views import homepage
from app.views.product_views import product_list, get_items_per_page, get_product_filter, get_order_days, export_product_list_to_excel, product_details_modal

router = routers.DefaultRouter()

urlpatterns = [
    path('', homepage, name='homepage'),
    path('products/', product_list, name='product_list'),
    path('get-items-per-page/', get_items_per_page, name='get_items_per_page'),
    path('get-order-days/', get_order_days, name='get_order_days'),  # Assuming this is the correct view for order days
    path('get-product-filter/', get_product_filter, name='get_product_filter'),
    path('export-product-list-to-excel/', export_product_list_to_excel, name='export_product_list_to_excel'),  # Assuming this is the correct view for exporting
    path('product-details-modal/<int:product_id>/', product_details_modal, name='product_details_modal'),
]

urlpatterns.append(path('api/', include(router.urls)))
