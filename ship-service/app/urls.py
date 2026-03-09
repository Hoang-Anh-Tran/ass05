from django.urls import path
from .views import ShippingProcess

urlpatterns = [
    path("", ShippingProcess.as_view(), name="shipping-process"),
]
