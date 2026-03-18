from django.urls import path
from .views import CommentListCreate, HealthView

urlpatterns = [
    path("", CommentListCreate.as_view(), name="comment-list-create"),
    path("health/", HealthView.as_view(), name="health"),
]
