from django.core.cache import cache
from django.conf import settings
from django.db.models import Count, Q

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action

from listing.models import Listing, UserProfile
from listing.serializers import (
    ListingDetailSerializer,
    ListingPublicSerializer,
    ListingOwnerSerializer,
    ListingCreateUpdateSerializer,
)

from rest_framework.pagination import PageNumberPagination

class ListingPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


def _get_bool_param(value):
    if value is None:
        return None
    value = str(value).strip().lower()
    if value in {"true", "1", "yes", "oui"}:
        return True
    if value in {"false", "0", "no", "non"}:
        return False
    return None


def _apply_listing_filters(queryset, params, *, include_status=False):
    search = params.get("search")
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(business__name__icontains=search)
        )

    for field in ("category", "ville", "commune", "quartier", "currency"):
        value = params.get(field)
        if value:
            queryset = queryset.filter(**{f"{field}__iexact": value})

    business_slug = params.get("business_slug")
    if business_slug:
        queryset = queryset.filter(business__slug=business_slug)

    barter = _get_bool_param(params.get("is_for_barter"))
    if barter is not None:
        queryset = queryset.filter(is_for_barter=barter)

    if include_status:
        active = _get_bool_param(params.get("is_active"))
        if active is not None:
            queryset = queryset.filter(is_active=active)

    min_price = params.get("min_price")
    if min_price:
        queryset = queryset.filter(price__gte=min_price)

    max_price = params.get("max_price")
    if max_price:
        queryset = queryset.filter(price__lte=max_price)

    return queryset


def _with_listing_metrics(queryset):
    return queryset.annotate(
        listing_views_count=Count(
            "analytics_events",
            filter=Q(analytics_events__event_type="listing_view"),
            distinct=True,
        ),
        whatsapp_clicks_count=Count(
            "analytics_events",
            filter=Q(analytics_events__event_type="whatsapp_click"),
            distinct=True,
        ),
    )


def _apply_listing_ordering(queryset, ordering, *, vendor=False):
    ordering = ordering or "recent"
    ordering_map = {
        "recent": ("-updated_at",),
        "price_asc": ("price", "-updated_at"),
        "price_desc": ("-price", "-updated_at"),
        "promoted": ("-is_promoted", "-updated_at"),
    }

    metric_orderings = {
        "popular": ("-listing_views_count", "-whatsapp_clicks_count", "-updated_at"),
        "views": ("-listing_views_count", "-updated_at"),
        "whatsapp_clicks": ("-whatsapp_clicks_count", "-updated_at"),
    }

    if ordering in metric_orderings and (vendor or ordering == "popular"):
        return _with_listing_metrics(queryset).order_by(*metric_orderings[ordering])

    return queryset.order_by(*ordering_map.get(ordering, ordering_map["recent"]))



# ============================
# PUBLIC LIST (HOME PAGE)
# ============================
class ListingListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ListingPublicSerializer
    pagination_class = ListingPagination

    def get_queryset(self):
        queryset = (
            Listing.objects.filter(is_active=True)
            .select_related("business", "business__owner")
            .prefetch_related("images", "analytics_events")
        )
        queryset = _apply_listing_filters(queryset, self.request.query_params)
        return _apply_listing_ordering(
            queryset,
            self.request.query_params.get("ordering"),
            vendor=False,
        )
    
    def list(self, request, *args, **kwargs):
        cache_key = f"listings_{request.query_params.urlencode()}_page_{request.query_params.get('page', 1)}"
        ttl = getattr(settings, "CACHE_TTL", 900)

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, ttl)
        return response



# ============================
# PUBLIC DETAIL (SINGLE VIEW)
# ============================
class ListingDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        cache_key = f"public_listing_detail_{slug}"
        ttl = getattr(settings, "CACHE_TTL", 900)

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        try:
            listing = Listing.objects.select_related("business").prefetch_related("images", "analytics_events").get(slug=slug, is_active=True)
            serializer = ListingDetailSerializer(listing)
            data = serializer.data
            cache.set(cache_key, data, ttl)
            return Response(data)
        except Listing.DoesNotExist:
            return Response({"error": "Annonce introuvable"}, status=404)


# ============================
# AUTHENTICATED VIEWSET
# ============================
class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet Listings (Dashboard vendeur)
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    CACHE_TTL = getattr(settings, "CACHE_TTL", 300)
    pagination_class = ListingPagination

    def get_queryset(self):
        business = getattr(self.request.user, 'business', None)
        if not business:
            return Listing.objects.none()
        queryset = (
            Listing.objects.filter(business=business)
            .select_related("business", "business__owner")
            .prefetch_related("images", "analytics_events")
        )
        queryset = _apply_listing_filters(
            queryset,
            self.request.query_params,
            include_status=True,
        )
        return _apply_listing_ordering(
            queryset,
            self.request.query_params.get("ordering"),
            vendor=True,
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ListingCreateUpdateSerializer
        if self.action == "retrieve":
            return ListingDetailSerializer
        if self.action == "my_listings":
            return ListingOwnerSerializer
        return ListingOwnerSerializer

    def _user_cache_key(self, user_id):
        return f"user_listings:{user_id}"

    def perform_create(self, serializer):
        user = self.request.user
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"phone_number": user.phone_whatsapp}
        )
        
        listing = serializer.save(business=user.business)
        cache.delete(self._user_cache_key(user.id))
        return listing

    def perform_update(self, serializer):
        listing = serializer.save()
        cache.delete(self._user_cache_key(self.request.user.id))
        return listing

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(self._user_cache_key(self.request.user.id))

    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        cache_key = self._user_cache_key(request.user.id)

        data = cache.get(cache_key)
        if data:
            return Response(data)

        queryset = self.get_queryset()

        # 🔥 IMPORTANT
        serializer = ListingOwnerSerializer(queryset, many=True)

        data = serializer.data
        cache.set(cache_key, data, self.CACHE_TTL)
        return Response(data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            "total": qs.count(),
            "active": qs.filter(is_active=True).count(),
        })
