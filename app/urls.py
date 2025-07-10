from django.urls import include, path
from rest_framework import routers
from app.views import static_views

router = routers.DefaultRouter()

urlpatterns = [
    path('', static_views.homepage, name='homepage'),

]

urlpatterns.append(path('api/', include(router.urls)))
