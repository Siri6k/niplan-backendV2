from http.client import responses

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Listing, Offer
from marketplace.serializers.offer import (
    OfferActionSerializer,
    OfferCreateSerializer,
    OfferReadSerializer,
)
from marketplace.services.offer_service import OfferService


@extend_schema(
    tags=["Marketplace"],
    summary="Faire une offre sur une annonce",
    description="POST : Faire une offre sur une annonce (acheteur authentifié).",
    responses={
        201: OfferReadSerializer,
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
    },
)
class ListingOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Lister les offres d'un listing (vendeur = tout, acheteur = ses offres)"""
        listing = get_object_or_404(Listing, pk=pk)
        user = request.user

        if listing.seller.user_id == user.id:
            offers = Offer.objects.filter(listing=listing)
        else:
            offers = Offer.objects.filter(listing=listing, buyer=user)

        offers = offers.select_related("buyer").order_by("-created_at")
        serializer = OfferReadSerializer(offers, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        listing = get_object_or_404(Listing, pk=pk)

        serializer = OfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer = OfferService.create_offer(
            buyer=request.user,
            listing=listing,
            **serializer.validated_data,
        )

        return Response(
            OfferReadSerializer(offer).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Marketplace"],
    summary="Gérer les offres",
    description="POST : Accepter, rejeter, annuler ou faire une contre-offre sur une offre (acheteur ou vendeur authentifié).",
    responses={
        200: OfferActionSerializer,
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
    },
)
class OfferActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = get_object_or_404(Offer, pk=pk)

        serializer = OfferActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]

        if action == "accept":
            offer = OfferService.accept_offer(
                offer=offer,
                user=request.user,
            )

        elif action == "reject":
            offer = OfferService.reject_offer(
                offer=offer,
                user=request.user,
            )

        elif action == "cancel":
            offer = OfferService.cancel_offer(
                offer=offer,
                user=request.user,
            )

        elif action == "counter":
            offer = OfferService.counter_offer(
                offer=offer,
                user=request.user,
                unit_amount=serializer.validated_data["unit_amount"],
                message=serializer.validated_data.get("message", ""),
            )

        return Response(OfferReadSerializer(offer).data)


@extend_schema(
    tags=["Marketplace"],
    summary="Liste des offres faites par l'utilisateur",
    description="GET : Récupérer la liste des offres faites par l'utilisateur authentifié.",
    responses={200: OfferReadSerializer(many=True)},
)
class MyOfferListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OfferReadSerializer

    def get_queryset(self):
        return Offer.objects.filter(buyer=self.request.user).select_related(
            "listing",
            "listing__store",
            "listing__variant",
            "listing__variant__product",
        )


@extend_schema(
    tags=["Marketplace"],
    summary="Liste des offres reçues par le vendeur",
    description="GET : Récupérer la liste des offres reçues par le vendeur authentifié.",
    responses={200: OfferReadSerializer(many=True)},
)
class SellerOfferListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OfferReadSerializer

    def get_queryset(self):
        return Offer.objects.filter(
            listing__seller__user=self.request.user
        ).select_related(
            "listing",
            "buyer",
            "listing__store",
            "listing__variant",
            "listing__variant__product",
        )
