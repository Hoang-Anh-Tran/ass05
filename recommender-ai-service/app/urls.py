from django.urls import path
from django.http import JsonResponse
from .views import HealthView

def index(request):
    return JsonResponse({
        "service": "recommender-ai-service",
        "message": "Recommender AI Service is running",
        "endpoints": ["/health/"]
    })

urlpatterns = [
    path("", index, name="index"),
    path("health/", HealthView.as_view(), name="health"),
]
