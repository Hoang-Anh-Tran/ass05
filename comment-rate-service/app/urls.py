from django.urls import path
from .views import CommentListCreate

urlpatterns = [
    path("", CommentListCreate.as_view(), name="comment-list-create"),
]
