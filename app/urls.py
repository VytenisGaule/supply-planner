from django.urls import path
from app.views import static_views

urlpatterns = [
    path('', static_views.homepage, name='homepage'),

]
