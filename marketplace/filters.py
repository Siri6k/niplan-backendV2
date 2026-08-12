# marketplace/filters.py

import django_filters

from marketplace.models import Listing


class ListingFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    category = django_filters.CharFilter(
        field_name="variant__product__category__slug",
    )
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    store = django_filters.UUIDFilter(field_name="store_id")
    currency = django_filters.CharFilter(field_name="currency")
    condition = django_filters.CharFilter(field_name="condition")

    class Meta:
        model = Listing
        fields = ["category", "location", "store", "currency", "condition"]
