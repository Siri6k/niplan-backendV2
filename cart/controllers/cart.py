# cart/views/cart.py

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import CartItem
from cart.serializers import (
    CartItemCreateSerializer,
    CartItemReadSerializer,
    CartItemUpdateSerializer,
    CartReadSerializer,
)
from cart.services.cart_service import CartService
from marketplace.models import Listing


@extend_schema(
    tags=["Cart"],
    summary="Mon panier",
    description="Retourne le panier actif du buyer connecté.",
    responses={200: CartReadSerializer},
)
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartService.get_active_cart_with_items(buyer=request.user)
        if cart is None:
            cart = CartService.get_or_create_active_cart(buyer=request.user)
        else:
            CartService.clean_cart(cart=cart)
            cart = CartService.get_active_cart_with_items(buyer=request.user)
        return Response(CartReadSerializer(cart).data, status=status.HTTP_200_OK)

    def delete(self, request):
        cart = CartService.clear_cart(buyer=request.user)
        return Response(CartReadSerializer(cart).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Cart"],
    summary="Ajouter un article au panier",
    description="Ajoute un Listing au panier du buyer connecté.",
    request=CartItemCreateSerializer,
    responses={201: CartItemReadSerializer, 400: "Bad Request"},
)
class CartItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = get_object_or_404(Listing, pk=serializer.validated_data["listing"])
        try:
            item = CartService.add_item(
                buyer=request.user,
                listing=listing,
                quantity=serializer.validated_data["quantity"],
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            CartItemReadSerializer(item).data, status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=["Cart"],
    summary="Modifier ou supprimer un article du panier",
    request=CartItemUpdateSerializer,
    responses={200: CartItemReadSerializer, 204: None, 400: "Bad Request"},
)
class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        item = get_object_or_404(
            CartItem.objects.select_related("cart", "listing"),
            pk=pk,
        )
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = CartService.update_item_quantity(
                buyer=request.user,
                item=item,
                quantity=serializer.validated_data["quantity"],
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CartItemReadSerializer(item).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        item = get_object_or_404(
            CartItem.objects.select_related("cart"),
            pk=pk,
        )
        try:
            CartService.remove_item(buyer=request.user, item=item)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
