from django.urls import path

from orders.controllers import (
    OrderListView,
    OrderCreateFromCartView,
    OrderDetailView,
    OrderCancelView,
    SellerOrderListView,
    SellerOrderDetailView,
    SellerOrderItemStatusView,
)

urlpatterns = [
    # Buyer endpoints
    path("", OrderListView.as_view(), name="order-list"),
    path(
        "from-cart/", OrderCreateFromCartView.as_view(), name="order-create-from-cart"
    ),
    path("<uuid:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<uuid:pk>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
    # Seller endpoints
    path("seller/", SellerOrderListView.as_view(), name="seller-order-list"),
    path(
        "seller/<uuid:pk>/", SellerOrderDetailView.as_view(), name="seller-order-detail"
    ),
    path(
        "seller/<uuid:order_id>/items/<uuid:item_id>/status/",
        SellerOrderItemStatusView.as_view(),
        name="seller-order-item-status",
    ),
]
