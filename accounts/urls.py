from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.controllers import (
    BecomeSellerView,
    LoginView,
    LogoutView,
    MeView,
    ProfileMeView,
    RegisterView,
    SellerMeView,
    StoreViewSet,
    TokenRefreshViewDoc,
)

app_name = "accounts"

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshViewDoc.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    # Profile
    path("profile/me/", ProfileMeView.as_view(), name="profile-me"),
    # Seller
    path("seller/become-seller/", BecomeSellerView.as_view(), name="become-seller"),
    path("seller/me/", SellerMeView.as_view(), name="seller-me"),
    # Store — mapping manuel pour éviter l'UUID dans l'URL
    path(
        "seller/store/",
        StoreViewSet.as_view(
            {
                "get": "retrieve",
                "post": "create",
                "patch": "partial_update",
            }
        ),
        name="store",
    ),
]
