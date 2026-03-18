from django.urls import path
from django.http import JsonResponse
from .views import RegisterView, LoginView, TokenRefreshView, TokenVerifyView, HealthView

def index(request):
    return JsonResponse({
        "service": "auth-service",
        "message": "Authentication Service is running",
        "endpoints": ["/register/", "/login/", "/token/refresh/", "/token/verify/", "/health/"]
    })

urlpatterns = [
    path("", index, name="index"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("health/", HealthView.as_view(), name="health"),
]
