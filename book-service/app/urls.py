from django.urls import path
from .views import BookListCreate, BookDetail

urlpatterns = [
    path("", BookListCreate.as_view()),      # handles /  (via API gateway)
    path("books/", BookListCreate.as_view()),  # handles /books/ (direct access)
    path("<int:pk>/", BookDetail.as_view()),    # handles /<id>/ (detail)
]