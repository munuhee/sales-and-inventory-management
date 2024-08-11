from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Purchase


@receiver(post_save, sender=Purchase)
def update_item_quantity(sender, instance, created, **kwargs):
    """
    Signal to update item quantity when a purchase is made.
    """
    if created:
        instance.item.quantity += instance.quantity
        instance.item.save()
