# catalog/urls.py

from django.urls import path

from catalog.controllers import (
    CategoryDetailView,
    CategoryListView,
    ProductDetailView,
    ProductListView,
    VariantDetailView,
)

app_name = "catalog"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"
    ),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("variants/<slug:sku>/", VariantDetailView.as_view(), name="variant-detail"),
]
