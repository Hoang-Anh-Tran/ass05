from django.urls import path
from .views import CustomerListCreate

urlpatterns = [
    path("", CustomerListCreate.as_view()),         # handles /  (via API gateway)
    path("customers/", CustomerListCreate.as_view()),  # handles /customers/ (direct access)
]