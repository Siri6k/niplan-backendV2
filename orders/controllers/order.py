from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import OrderReadSerializer
from orders.services import OrderService

# ============================================================
# LISTE DES COMMANDES DE L'UTILISATEUR
# ============================================================


@extend_schema(
    tags=["Orders"],
    summary="Mes commandes",
    responses={200: OrderReadSerializer(many=True)},
)
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects.filter(buyer=request.user)
            .prefetch_related(
                "items",
                "items__listing",
                "items__listing__store",
                "items__listing__variant",
                "items__listing__variant__product",
            )
            .order_by("-created_at")
        )
        serializer = OrderReadSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# CRÉATION D'UNE COMMANDE À PARTIR DU PANIER
# ============================================================


@extend_schema(
    tags=["Orders"],
    summary="Créer une commande à partir du panier",
    responses={
        201: OrderReadSerializer,
        400: {"description": "Panier invalide"},
    },
)
class OrderCreateFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # create_order_from_cart renvoie une liste d'ordres (multi‑vendeurs)
            orders = OrderService.create_orders_from_cart(buyer=request.user)
        except ValidationError as e:
            return Response(
                {"detail": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Si une seule commande, on la retourne directement
        # Sinon, on peut retourner la liste ou la première
        # Pour simplifier, on retourne la première commande (ou on peut retourner toutes)
        # Adaptez selon vos besoins frontend
        if len(orders) == 1:
            serializer = OrderReadSerializer(orders[0])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Multi‑vendeurs : retourner la liste des commandes créées
            serializer = OrderReadSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================================
# DÉTAIL D'UNE COMMANDE
# ============================================================


@extend_schema(
    tags=["Orders"],
    summary="Détail d'une commande",
    responses={
        200: OrderReadSerializer,
        404: {"description": "Commande introuvable"},
    },
)
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = OrderService.get_order(buyer=request.user, order_id=pk)
        if order is None:
            return Response(
                {"detail": "Commande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = OrderReadSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# ANNULATION D'UNE COMMANDE
# ============================================================


@extend_schema(
    tags=["Orders"],
    summary="Annuler une commande",
    responses={
        200: OrderReadSerializer,
        400: {"description": "Commande non annulable"},
        404: {"description": "Commande introuvable"},
    },
)
class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            order = OrderService.cancel_order(buyer=request.user, order_id=pk)
        except ValidationError as e:
            # Distinguer "introuvable" des autres erreurs
            if str(e) == "Commande introuvable.":
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {"detail": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderReadSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
