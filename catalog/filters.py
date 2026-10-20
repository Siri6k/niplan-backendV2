import django_filters as df
from catalog.models import ProductVariant


class VariantFilter(df.FilterSet):
    sku = df.CharFilter(lookup_expr="iexact")
    is_active = df.BooleanFilter()
    product = df.UUIDFilter(field_name="product_id")
    attribute = df.CharFilter(method="filter_attribute")

    class Meta:
        model = ProductVariant
        # ⚠️ "variant" n'existe pas sur ProductVariant → ne pas le mettre
        fields = ["sku", "is_active", "product"]

    def filter_attribute(self, qs, name, value):
        if ":" not in value:
            return qs
        attr, val = value.split(":", 1)
        return qs.filter(
            # ✅ `variant_values`, pas `variant`
            variant_values__value__attribute__name__iexact=attr.strip(),
            variant_values__value__value__iexact=val.strip(),
        ).distinct()
