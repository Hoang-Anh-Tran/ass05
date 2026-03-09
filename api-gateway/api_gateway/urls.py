from django.contrib import admin
from django.urls import path, re_path
from app import views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    
    # Use re_path to capture any trailing path (making the slash and path optional)
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