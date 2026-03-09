from django.urls import path
from .views import manage_books

urlpatterns = [
    path("", manage_books, name="manage-books"),
    path("<int:book_id>/", manage_books, name="manage-books-detail"),
]
