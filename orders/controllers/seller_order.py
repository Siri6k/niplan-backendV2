from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import SellerOrderSerializer
from orders.services.seller_order_service import SellerOrderService


class SellerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Seller Orders"],
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
        tags=["Seller Orders"],
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
