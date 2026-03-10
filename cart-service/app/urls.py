from django.urls import path
from .views import CartCreate, AddCartItem, ViewCart, ModifyCartItem, ClearCart

urlpatterns = [
    path("", CartCreate.as_view(), name="cart-create"),
    path("items/", AddCartItem.as_view(), name="add-cart-item"),
    path("items/<int:item_id>/", ModifyCartItem.as_view(), name="modify-cart-item"),
    path("<int:customer_id>/", ViewCart.as_view(), name="view-cart"),
    path("clear/<int:customer_id>/", ClearCart.as_view(), name="clear-cart"),
]