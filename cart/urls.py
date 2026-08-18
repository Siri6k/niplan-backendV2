# cart/urls.py

from django.urls import path

from cart.controllers import (
    CartView,
    CartItemCreateView,
    CartItemDetailView,
)

app_name = "cart"

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("items/", CartItemCreateView.as_view(), name="cart-item-create"),
    path("items/<uuid:pk>/", CartItemDetailView.as_view(), name="cart-item-detail"),
]
