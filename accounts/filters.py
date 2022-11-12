import django_filters
from .models import Profile

class StaffFilter(django_filters.FilterSet):
    class Meta:
        model = Profile
        fields = ['user', 'email', 'role', 'status']