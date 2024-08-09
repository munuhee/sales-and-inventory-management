import django_filters
from .models import Profile


class StaffFilter(django_filters.FilterSet):
    """Filter set for the Profile model to refine staff searches."""

    class Meta:
        """Meta options for the StaffFilter."""
        model = Profile
        fields = ['user', 'email', 'role', 'status']
