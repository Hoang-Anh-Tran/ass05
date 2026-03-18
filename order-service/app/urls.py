from django.urls import path
from .views import OrderCreate, OrderList, OrderDetail, HealthView

urlpatterns = [
    path("", OrderCreate.as_view(), name="order-create"),
    path("list/", OrderList.as_view(), name="order-list"),
    path("<int:order_id>/", OrderDetail.as_view(), name="order-detail"),
    path("health/", HealthView.as_view(), name="health"),
]
