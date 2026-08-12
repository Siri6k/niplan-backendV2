from rest_framework import generics, permissions

from accounts.models import Profile
from accounts.serializers import ProfileSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    tags=["Profiles"],
    summary="Mon profil",
    description="Récupère ou modifie le profil acheteur (avatar, bio, ville, etc.). Les champs email/password sont en lecture seule.",
    request=ProfileSerializer,
    responses={200: ProfileSerializer},
)
class ProfileMeView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
