from django.urls import include, path
from rest_framework import routers
from app.views.static_views import homepage
from app.views.product_views import product_list, get_items_per_page, get_product_filter

router = routers.DefaultRouter()

urlpatterns = [
    path('', homepage, name='homepage'),
    path('products/', product_list, name='product_list'),
    path('get-items-per-page/', get_items_per_page, name='get_items_per_page'),
    path('get-product-filter/', get_product_filter, name='get_product_filter'),

]

urlpatterns.append(path('api/', include(router.urls)))
