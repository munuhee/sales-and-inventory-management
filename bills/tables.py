import django_tables2 as tables

from .models import Bill


class BillTable(tables.Table):
    class Meta:
        model = Bill
        fields = (
            'date', 'institution_name', 'phone_number', 'email', 'address',
            'description', 'payment_details', 'amount', 'status',
        )
