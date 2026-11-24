from django.conf import settings


def business(request):
    """Expose business details (name, address, currency) to all templates."""
    return {'business': settings.BUSINESS}
