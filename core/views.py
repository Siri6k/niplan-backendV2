# core/views.py

from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


@extend_schema(
    tags=["Core"],
    summary="Health check",
    description="Vérifie la disponibilité du système, de la base de données et du cache.",
    responses={
        200: OpenApiResponse(description="Tous les services sont opérationnels"),
        503: OpenApiResponse(description="Un ou plusieurs services sont dégradés"),
    },
)
class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = []

    def get(self, request):
        health_data = {
            "status": "healthy",
            "database": "connected",
            "cache": "connected",
            "timestamp": timezone.now().isoformat(),
        }
        status_code = status.HTTP_200_OK

        # 1. Vérification base de données
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            health_data["database"] = f"unreachable: {str(e)}"
            health_data["status"] = "unhealthy"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        # 2. Vérification cache (Redis / LocMem)
        try:
            cache_key = "__healthcheck__"
            cache.set(cache_key, "ok", timeout=10)
            if cache.get(cache_key) != "ok":
                raise ValueError("Cache read/write mismatch")
        except Exception as e:
            health_data["cache"] = f"unreachable: {str(e)}"
            health_data["status"] = "unhealthy"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(health_data, status=status_code)
