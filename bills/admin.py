from django.contrib import admin
from .models import Bill


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Admin interface for managing Bill instances."""

    readonly_fields = ('date',)
    list_filter = ('status',)
    search_fields = ('institution_name', 'description')
    fields = (
        'date',
        'institution_name',
        'phone_number',
        'email',
        'address',
        'description',
        'payment_details',
        'amount',
        'status'
    )

    list_display = (
        'slug',
        'date',
        'institution_name',
        'phone_number',
        'email',
        'address',
        'description',
        'payment_details',
        'amount',
        'status'
    )
