from django.urls import path
from django.http import JsonResponse
from .views import VoucherListCreate, VoucherDetail, HealthView

def index(request):
    return JsonResponse({
        "service": "catalog-service",
        "message": "Catalog Service is running",
        "endpoints": ["/vouchers/", "/vouchers/<id>/", "/health/"]
    })

urlpatterns = [
    path("", index, name="index"),
    path("vouchers/", VoucherListCreate.as_view(), name="voucher-list-create"),
    path("vouchers/<int:pk>/", VoucherDetail.as_view(), name="voucher-detail"),
    path("health/", HealthView.as_view(), name="health"),
]
