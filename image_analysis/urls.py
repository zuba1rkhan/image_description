from django.urls import path
from .views import describe_image, health_check

urlpatterns = [
    path('describe/', describe_image, name='describe_image'),
    path('health/', health_check, name='health_check'),
]