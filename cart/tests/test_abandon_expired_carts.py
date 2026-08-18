# cart/tests/test_abandon_expired_carts.py

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from cart.models import Cart


class AbandonExpiredCartsCommandTests(TestCase):
    def setUp(self):
        # Acheteur avec panier récent (doit rester actif)
        self.buyer_recent = User.objects.create_user(
            email="buyer_recent@niplan.com",
            password="TestPassword123!",
        )
        # Acheteur avec panier ancien (doit être abandonné)
        self.buyer_old = User.objects.create_user(
            email="buyer_old@niplan.com",
            password="TestPassword123!",
        )

    def test_command_marks_old_active_carts_as_abandoned(self):
        # Panier actif récent (acheteur_recent)
        recent_cart = Cart.objects.create(
            buyer=self.buyer_recent,
            status=Cart.Status.ACTIVE,
            last_accessed_at=timezone.now(),
        )

        # Panier actif ancien (acheteur_old)
        old_date = timezone.now() - timedelta(days=31)
        old_cart = Cart.objects.create(
            buyer=self.buyer_old,
            status=Cart.Status.ACTIVE,
            last_accessed_at=old_date,
        )

        # Exécuter la commande avec un seuil de 30 jours
        call_command("abandon_expired_carts", days=30)

        recent_cart.refresh_from_db()
        old_cart.refresh_from_db()

        self.assertEqual(recent_cart.status, Cart.Status.ACTIVE)
        self.assertEqual(old_cart.status, Cart.Status.ABANDONED)

    def test_command_custom_days(self):
        # Panier actif ancien (acheteur_old) inactif depuis 10 jours
        old_date = timezone.now() - timedelta(days=10)
        cart = Cart.objects.create(
            buyer=self.buyer_old,
            status=Cart.Status.ACTIVE,
            last_accessed_at=old_date,
        )

        # Seuil de 5 jours : doit être abandonné
        call_command("abandon_expired_carts", days=5)
        cart.refresh_from_db()
        self.assertEqual(cart.status, Cart.Status.ABANDONED)

    def test_command_does_not_abandon_recent_cart(self):
        # Panier actif récent (acheteur_recent)
        cart = Cart.objects.create(
            buyer=self.buyer_recent,
            status=Cart.Status.ACTIVE,
            last_accessed_at=timezone.now(),
        )
        call_command("abandon_expired_carts", days=30)
        cart.refresh_from_db()
        self.assertEqual(cart.status, Cart.Status.ACTIVE)
