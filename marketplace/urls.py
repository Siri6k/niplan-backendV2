# marketplace/urls.py

from django.urls import path

from marketplace.controllers import (
    ListingActionView,
    ListingDetailView,
    ListingListView,
    MyListingListView,
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
]
