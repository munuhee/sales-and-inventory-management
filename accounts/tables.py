import django_tables2 as tables

from .models import Profile


class ProfileTable(tables.Table):
    class Meta:
        model = Profile
        fields = ('user', 'first_name', 'last_name', 'email', 'telephone', 'role', 'status')
