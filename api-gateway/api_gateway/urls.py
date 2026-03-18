from django.contrib import admin
from django.urls import path, re_path
from app import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Swagger Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    
    # Observability
    path("health/", views.health, name="health"),
    path("metrics/", views.metrics, name="metrics"),
    
    # Auth service
    re_path(r'^auth/?(?P<path>.*)$', views.auth, name="auth"),
    
    # Service proxies
    re_path(r'^customers/?(?P<path>.*)$', views.customers, name="customers"),
    re_path(r'^books/?(?P<path>.*)$', views.books, name="books"),
    re_path(r'^cart/?(?P<path>.*)$', views.cart, name="cart"),
    re_path(r'^staff/?(?P<path>.*)$', views.staff, name="staff"),
    re_path(r'^manager/?(?P<path>.*)$', views.manager, name="manager"),
    re_path(r'^catalog/?(?P<path>.*)$', views.catalog, name="catalog"),
    re_path(r'^orders/?(?P<path>.*)$', views.orders, name="orders"),
    re_path(r'^shipping/?(?P<path>.*)$', views.shipping, name="shipping"),
    re_path(r'^payment/?(?P<path>.*)$', views.payment, name="payment"),
    re_path(r'^comments/?(?P<path>.*)$', views.comments, name="comments"),
    re_path(r'^recommendations/?(?P<path>.*)$', views.recommendations, name="recommendations"),
]