from django.urls import path
from .views import BookListCreate

urlpatterns = [
    path("", BookListCreate.as_view()),      # handles /  (via API gateway)
    path("books/", BookListCreate.as_view()),  # handles /books/ (direct access)
]