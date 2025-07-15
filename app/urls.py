from django.urls import include, path
from rest_framework import routers
from app.views import static_views
from app.views.product_views import product_list

router = routers.DefaultRouter()

urlpatterns = [
    path('', static_views.homepage, name='homepage'),
    path('products/', product_list, name='product_list'),

]

urlpatterns.append(path('api/', include(router.urls)))
