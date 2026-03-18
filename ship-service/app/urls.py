from django.urls import path
from .views import ShippingProcess, ShippingReserve, ShippingCancel, FaultEnable, FaultDisable, HealthView

urlpatterns = [
    path("", ShippingProcess.as_view(), name="shipping-process"),
    path("reserve/", ShippingReserve.as_view(), name="shipping-reserve"),
    path("cancel/", ShippingCancel.as_view(), name="shipping-cancel"),
    path("fault/enable/", FaultEnable.as_view(), name="fault-enable"),
    path("fault/disable/", FaultDisable.as_view(), name="fault-disable"),
    path("health/", HealthView.as_view(), name="health"),
]
