# catalog/urls.py

from django.urls import path

from catalog.controllers import (
    CategoryDetailView,
    CategoryListView,
    ProductDetailView,
    ProductListView,
    VariantDetailView,
    VariantListView,
    ProductVariantsView,
    VariantAutocompleteView,
    VariantBulkLookupView,
    VariantBySkuView,
    VariantFacetsView,
)

app_name = "catalog"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"
    ),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    # ---------- Variantes ----------
    path("variants/", VariantListView.as_view(), name="variant-list"),
    path("variants/<uuid:id>/", VariantDetailView.as_view(), name="variant-detail"),
    path("variants/sku/<str:sku>/", VariantBySkuView.as_view(), name="variant-by-sku"),
    path(
        "products/<uuid:product_id>/variants/",
        ProductVariantsView.as_view(),
        name="product-variants",
    ),
    path(
        "variants/autocomplete/",
        VariantAutocompleteView.as_view(),
        name="variant-autocomplete",
    ),
    path(
        "variants/bulk-lookup/",
        VariantBulkLookupView.as_view(),
        name="variant-bulk-lookup",
    ),
    path(
        "variants/facets/",
        VariantFacetsView.as_view(),
        name="variant-facets",
    ),
]
