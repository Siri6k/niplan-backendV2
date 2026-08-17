# marketplace/urls.py

from django.urls import path

from marketplace.controllers import (
    ListingActionView,
    ListingDetailView,
    ListingListView,
    MyListingListView,
    FavoriteListView,
    ListingFavoriteView,
    OfferActionView,
    ListingOfferView,
    MyOfferListView,
    SellerOfferListView,
)

app_name = "marketplace"

urlpatterns = [
    path("listings/", ListingListView.as_view(), name="listing-list"),
    path("my-listings/", MyListingListView.as_view(), name="my-listings"),
    path("listings/<uuid:pk>/", ListingDetailView.as_view(), name="listing-detail"),
    path(
        "listings/<uuid:pk>/actions/",
        ListingActionView.as_view(),
        name="listing-actions",
    ),
    path(
        "favorites/",
        FavoriteListView.as_view(),
        name="favorite-list",
    ),
    path(
        "listings/<uuid:pk>/favorite/",
        ListingFavoriteView.as_view(),
        name="listing-favorite",
    ),
    path(
        "listings/<uuid:pk>/offers/",
        ListingOfferView.as_view(),
        name="listing-offers",
    ),
    path(
        "offers/<uuid:pk>/actions/",
        OfferActionView.as_view(),
        name="offer-actions",
    ),
    path(
        "my-offers/",
        MyOfferListView.as_view(),
        name="my-offers",
    ),
    path(
        "seller/offers/",
        SellerOfferListView.as_view(),
        name="seller-offers",
    ),
]
