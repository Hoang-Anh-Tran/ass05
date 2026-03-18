from django.urls import path
from .views import CustomerListCreate, CustomerLogin, HealthView

urlpatterns = [
    path("", CustomerListCreate.as_view(), name="customer-list-create"),
    path("login/", CustomerLogin.as_view(), name="customer-login"),
    path("health/", HealthView.as_view(), name="health"),
]