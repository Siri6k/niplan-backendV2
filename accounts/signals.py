# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Profile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un Profile à la création d'un User."""
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le Profile lors de la sauvegarde du User."""
    if hasattr(instance, "profile"):
        instance.profile.save()
