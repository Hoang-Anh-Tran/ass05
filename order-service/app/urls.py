from django.urls import path
from .views import OrderCreate, OrderList

urlpatterns = [
    path("", OrderCreate.as_view(), name="order-create"),
    path("list/", OrderList.as_view(), name="order-list"),
]
