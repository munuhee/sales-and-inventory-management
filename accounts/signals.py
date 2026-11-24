from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """
    Every user gets a staff profile. Superusers are activated as Admin so the
    first account can always sign in; everyone else starts Inactive and waits
    for approval.
    """
    defaults = {}
    if instance.is_superuser:
        defaults.update(status='A', role='AD')
    profile, made = Profile.objects.get_or_create(user=instance, defaults=defaults)
    if not made and instance.is_superuser and (profile.status != 'A' or profile.role != 'AD'):
        Profile.objects.filter(pk=profile.pk).update(status='A', role='AD')
