from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError

from orders.serializers import (
    SellerOrderSerializer,
    SellerOrderItemSerializer,
    SellerOrderItemStatusSerializer,
)
from orders.services import SellerOrderService, OrderStatusService


class SellerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Orders"],
        summary="Commandes du vendeur",
        responses={200: SellerOrderSerializer(many=True)},
    )
    def get(self, request):
        orders = SellerOrderService.get_seller_orders(seller_user=request.user)
        serializer = SellerOrderSerializer(
            orders, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SellerOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Orders"],
        summary="Détail d'une commande vendeur",
        responses={200: SellerOrderSerializer},
    )
    def get(self, request, pk):
        order = SellerOrderService.get_seller_order(
            seller_user=request.user, order_id=pk
        )
        if order is None:
            return Response(
                {"detail": "Commande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SellerOrderSerializer(order, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SellerOrderItemStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Orders"],
        summary="Modifier le statut d'un article",
        request=SellerOrderItemStatusSerializer,
        responses={
            200: SellerOrderItemSerializer,
            400: {"description": "Transition invalide"},
            404: {"description": "Article introuvable"},
        },
    )
    def patch(self, request, order_id, item_id):
        serializer = SellerOrderItemStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            item = OrderStatusService.update_item_status(
                seller_user=request.user,
                order_id=order_id,
                item_id=item_id,
                new_status=serializer.validated_data["status"],
            )
        except ValidationError as e:
            return Response(
                {"detail": e.messages if hasattr(e, "messages") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            SellerOrderItemSerializer(item).data,
            status=status.HTTP_200_OK,
        )
