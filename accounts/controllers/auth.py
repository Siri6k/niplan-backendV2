from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.serializers import RegisterSerializer, UserMeSerializer
from accounts.serializers.auth import CustomTokenObtainPairSerializer

from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

User = get_user_model()


@extend_schema(
    tags=["Auth"],
    summary="Inscription",
    description="Crée un compte utilisateur avec email et mot de passe. Un Profile est créé automatiquement.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Utilisateur créé"),
        400: OpenApiResponse(description="Données invalides"),
    },
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(
    tags=["Auth"],
    summary="Connexion",
    description="Retourne un access token, un refresh token et les infos utilisateur.",
    request=CustomTokenObtainPairSerializer,
    responses={
        200: OpenApiResponse(description="Tokens générés"),
        401: OpenApiResponse(description="Identifiants invalides"),
    },
)
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Auth"],
    summary="Déconnexion",
    description="Blacklist le refresh token pour invalider la session.",
    request={
        "application/json": {
            "type": "object",
            "properties": {"refresh": {"type": "string"}},
        }
    },
    responses={
        205: OpenApiResponse(description="Déconnexion réussie"),
        400: OpenApiResponse(description="Token invalide ou manquant"),
    },
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT
            )
        except KeyError:
            return Response(
                {"detail": "Le champ 'refresh' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=["Auth"],
    summary="Identité connectée",
    description="Retourne l'utilisateur actuellement authentifié (id, email, is_seller...).",
    responses={200: UserMeSerializer},
)
class MeView(generics.RetrieveAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Auth"],
    summary="Rafraîchir le token",
    description="Envoie un refresh token valide pour obtenir un nouveau access token. L'ancien access token devient invalide.",
    request=TokenRefreshSerializer,
    responses={
        200: OpenApiResponse(
            description="Nouveau access token généré",
            response={
                "type": "object",
                "properties": {
                    "access": {
                        "type": "string",
                        "description": "Nouveau JWT access token",
                    },
                    "refresh": {
                        "type": "string",
                        "description": "Nouveau refresh token (si ROTATE_REFRESH_TOKENS=True)",
                    },
                },
            },
        ),
        401: OpenApiResponse(
            description="Refresh token invalide, expiré ou blacklisté"
        ),
    },
)
class TokenRefreshViewDoc(TokenRefreshView):
    """Wrapper pour que Spectacular documente le refresh token."""

    pass
