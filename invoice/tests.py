from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from InventoryMS.test_utils import make_item, make_user

from .models import Invoice


class InvoiceTests(TestCase):
    def setUp(self):
        self.item = make_item()

    def make(self, **kwargs):
        data = dict(customer_name='Acme', contact_number='0700', item=self.item,
                    price_per_item=Decimal('19.99'), quantity=Decimal('3'), shipping=Decimal('5'))
        data.update(kwargs)
        return Invoice.objects.create(**data)

    def test_totals_are_exact_decimals(self):
        invoice = self.make()
        self.assertEqual(invoice.total, Decimal('59.97'))
        self.assertEqual(invoice.grand_total, Decimal('64.97'))

    def test_slug_and_number(self):
        invoice = self.make()
        self.assertTrue(invoice.slug.startswith('acme'))
        self.assertEqual(invoice.invoice_number, f'INV{invoice.pk:06d}')

    def test_date_does_not_change_on_edit(self):
        invoice = self.make()
        created = invoice.date
        invoice.customer_name = 'Acme Ltd'
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(invoice.date, created)

    def test_detail_and_pdf_require_login(self):
        invoice = self.make()
        for name in ('invoice-detail', 'invoice-pdf'):
            response = self.client.get(reverse(name, args=[invoice.slug]))
            self.assertEqual(response.status_code, 302, name)

    def test_operative_can_view_but_not_edit(self):
        invoice = self.make()
        self.client.force_login(make_user('op'))
        self.assertEqual(self.client.get(reverse('invoice-detail', args=[invoice.slug])).status_code, 200)
        self.assertEqual(self.client.get(reverse('invoice-update', args=[invoice.slug])).status_code, 403)
