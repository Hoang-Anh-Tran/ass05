from django.urls import path
from .views import PaymentProcess, PaymentReserve, PaymentCancel, FaultEnable, FaultDisable, HealthView

urlpatterns = [
    path("", PaymentProcess.as_view(), name="payment-process"),
    path("reserve/", PaymentReserve.as_view(), name="payment-reserve"),
    path("cancel/", PaymentCancel.as_view(), name="payment-cancel"),
    path("fault/enable/", FaultEnable.as_view(), name="fault-enable"),
    path("fault/disable/", FaultDisable.as_view(), name="fault-disable"),
    path("health/", HealthView.as_view(), name="health"),
]
