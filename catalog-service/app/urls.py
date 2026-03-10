from django.urls import path
from .views import VoucherListCreate, VoucherDetail

urlpatterns = [
    path("vouchers/", VoucherListCreate.as_view(), name="voucher-list-create"),
    path("vouchers/<int:pk>/", VoucherDetail.as_view(), name="voucher-detail"),
]
