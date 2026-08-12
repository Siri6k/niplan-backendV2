# core/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # API schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Apps
    path("api/v1/accounts/", include("accounts.urls", namespace="accounts")),
    path("api/v1/catalog/", include("catalog.urls", namespace="catalog")),
    path("api/v1/marketplace/", include("marketplace.urls", namespace="marketplace")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
