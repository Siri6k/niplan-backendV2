# marketplace/views/listing.py

from django.shortcuts import get_object_or_404
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from marketplace.filters import ListingFilter
from marketplace.models import Listing
from marketplace.serializers import (
    ListingActionSerializer,
    ListingCreateSerializer,
    ListingReadSerializer,
    ListingUpdateSerializer,
)
from marketplace.services.listing_service import ListingService


@extend_schema(
    tags=["Marketplace"],
    summary="Liste et création d'annonces",
    description="GET : liste publique des annonces PUBLISHED (filtrable, paginée). POST : créer une annonce (vendeur authentifié).",
    responses={200: ListingReadSerializer(many=True), 201: ListingReadSerializer},
)
class ListingListView(ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ListingFilter
    search_fields = [
        "title",
        "description",
        "variant__product__name",
        "variant__product__brand",
        "variant__sku",
        "store__name",
    ]
    ordering_fields = ["price", "created_at", "published_at"]
    ordering = ["-published_at"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Listing.objects.filter(status=Listing.Status.PUBLISHED).select_related(
            "seller",
            "store",
            "variant",
            "variant__product",
            "variant__product__category",
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ListingCreateSerializer
        return ListingReadSerializer

    def perform_create(self, serializer):
        self.created_listing = ListingService.create_listing(
            user=self.request.user,
            **serializer.validated_data,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            ListingReadSerializer(self.created_listing).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Marketplace"],
    summary="Détail, modification, suppression d'une annonce",
    description="GET : détail public (ou propriétaire si brouillon). PATCH : modifier (owner only, pas ARCHIVED). DELETE : supprimer (DRAFT only).",
    responses={200: ListingReadSerializer},
)
class ListingDetailView(RetrieveUpdateDestroyAPIView):
    lookup_field = "pk"

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Listing.objects.select_related(
            "seller", "store", "variant", "variant__product"
        )

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return ListingUpdateSerializer
        return ListingReadSerializer

    def get_object(self):
        listing = super().get_object()

        if self.request.method == "GET":
            if listing.status != Listing.Status.PUBLISHED:
                user = self.request.user
                if not user.is_authenticated or listing.seller.user_id != user.id:
                    raise Http404("Aucune annonce ne correspond à votre requête.")
        return listing

    def perform_update(self, serializer):
        self.updated_listing = ListingService.update_listing(
            listing=self.get_object(),
            user=self.request.user,
            **serializer.validated_data,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(ListingReadSerializer(self.updated_listing).data)

    def perform_destroy(self, instance):
        if instance.status != Listing.Status.DRAFT:
            raise ValidationError("Seule une annonce en brouillon peut être supprimée.")
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.seller.user_id != request.user.id:
            return Response(
                {"detail": "Vous ne pouvez pas supprimer cette annonce."},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Marketplace"],
    summary="Actions workflow (publish, pause, archive)",
    description="Publier, mettre en pause ou archiver une annonce.",
    request=ListingActionSerializer,
    responses={200: ListingReadSerializer},
)
class ListingActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        listing = get_object_or_404(Listing, pk=pk)

        serializer = ListingActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]

        if action == "publish":
            listing = ListingService.publish_listing(listing=listing, user=request.user)
        elif action == "pause":
            listing = ListingService.pause_listing(listing=listing, user=request.user)
        elif action == "archive":
            listing = ListingService.archive_listing(listing=listing, user=request.user)

        return Response(ListingReadSerializer(listing).data)


@extend_schema(
    tags=["Marketplace"],
    summary="Mes annonces",
    description="Retourne toutes les annonces du vendeur connecté (tous statuts : DRAFT, PUBLISHED, PAUSED, ARCHIVED).",
    responses={200: ListingReadSerializer(many=True)},
)
class MyListingListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListingReadSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["price", "created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Listing.objects.filter(seller__user=self.request.user).select_related(
            "seller", "store", "variant", "variant__product"
        )
