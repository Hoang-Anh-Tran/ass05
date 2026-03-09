from django.urls import path
from .views import PaymentProcess

urlpatterns = [
    path("", PaymentProcess.as_view(), name="payment-process"),
]
