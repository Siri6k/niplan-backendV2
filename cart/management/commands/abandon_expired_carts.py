from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from cart.models import Cart


class Command(BaseCommand):
    help = "Marque comme abandonnés les paniers actifs sans activité depuis plus de X jours."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Nombre de jours d'inactivité avant abandon (défaut: 30)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        threshold = timezone.now() - timedelta(days=days)

        expired_carts = Cart.objects.filter(
            status=Cart.Status.ACTIVE,
            last_accessed_at__lt=threshold,
        )

        count = expired_carts.update(status=Cart.Status.ABANDONED)

        self.stdout.write(
            self.style.SUCCESS(f"{count} panier(s) marqué(s) comme abandonné(s).")
        )
