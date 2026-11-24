import json
from decimal import Decimal
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from InventoryMS.test_utils import PASSWORD, make_customer, make_item, make_user, make_vendor
from store.models import Item

from .models import LoyaltyTransaction, Purchase, Sale
from .services import create_sale, void_sale


def weasyprint_available():
    try:
        import weasyprint  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


LOYALTY = {'enabled': True, 'earn_per': '100', 'point_value': '1.00', 'min_redeem': 0}


@override_settings(LOYALTY=LOYALTY)
class CreateSaleServiceTests(TestCase):
    def setUp(self):
        self.cashier = make_user('cashier')
        self.customer = make_customer()
        self.soda = make_item('Soda', quantity=10, price='50.00')
        self.chips = make_item('Chips', quantity=5, price='120.50')

    def sell(self, items, **kwargs):
        kwargs.setdefault('amount_paid', '100000')
        return create_sale(user=self.cashier, customer_id=self.customer.pk, items=items, **kwargs)

    def test_prices_come_from_the_database_not_the_client(self):
        sale = self.sell([{'id': self.soda.pk, 'quantity': 2, 'price': '0.01', 'total_item': '0.02'}])
        self.assertEqual(sale.sub_total, Decimal('100.00'))
        self.assertEqual(sale.saledetail_set.get().price, Decimal('50.00'))

    def test_totals_tax_and_change(self):
        sale = self.sell(
            [{'id': self.soda.pk, 'quantity': 1}, {'id': self.chips.pk, 'quantity': 2}],
            tax_percentage='16', amount_paid='400',
        )
        self.assertEqual(sale.sub_total, Decimal('291.00'))
        self.assertEqual(sale.tax_amount, Decimal('46.56'))
        self.assertEqual(sale.grand_total, Decimal('337.56'))
        self.assertEqual(sale.amount_change, Decimal('62.44'))
        self.assertEqual(sale.served_by, self.cashier)

    def test_stock_is_reduced(self):
        self.sell([{'id': self.soda.pk, 'quantity': 3}])
        self.soda.refresh_from_db()
        self.assertEqual(self.soda.quantity, 7)

    def test_duplicate_lines_are_merged(self):
        sale = self.sell([{'id': self.soda.pk, 'quantity': 2}, {'id': self.soda.pk, 'quantity': 3}])
        self.assertEqual(sale.saledetail_set.get().quantity, 5)

    def test_cannot_oversell(self):
        with self.assertRaisesMessage(ValidationError, 'Not enough stock'):
            self.sell([{'id': self.soda.pk, 'quantity': 11}])
        self.soda.refresh_from_db()
        self.assertEqual(self.soda.quantity, 10)
        self.assertFalse(Sale.objects.exists())

    def test_rejects_bad_quantities(self):
        for qty in (0, -1, '1.5', 'abc'):
            with self.subTest(qty=qty), self.assertRaises(ValidationError):
                self.sell([{'id': self.soda.pk, 'quantity': qty}])

    def test_rejects_underpayment(self):
        with self.assertRaisesMessage(ValidationError, 'less than the total'):
            self.sell([{'id': self.soda.pk, 'quantity': 1}], amount_paid='49.99')

    def test_rejects_empty_cart_and_unknown_customer(self):
        with self.assertRaises(ValidationError):
            self.sell([])
        with self.assertRaises(ValidationError):
            create_sale(user=self.cashier, customer_id=999, items=[{'id': self.soda.pk, 'quantity': 1}],
                        amount_paid='100')

    def test_failed_line_rolls_back_whole_sale(self):
        with self.assertRaises(ValidationError):
            self.sell([{'id': self.soda.pk, 'quantity': 1}, {'id': 99999, 'quantity': 1}])
        self.soda.refresh_from_db()
        self.assertEqual(self.soda.quantity, 10)


@override_settings(LOYALTY=LOYALTY)
class LoyaltyTests(TestCase):
    def setUp(self):
        self.cashier = make_user('cashier')
        self.customer = make_customer(points=0)
        self.item = make_item('TV', quantity=5, price='1000.00')

    def test_points_are_earned_on_net_spend(self):
        sale = create_sale(user=self.cashier, customer_id=self.customer.pk,
                           items=[{'id': self.item.pk, 'quantity': 1}],
                           tax_percentage='16', amount_paid='2000')
        self.customer.refresh_from_db()
        self.assertEqual(sale.loyalty_points_earned, 10)  # 1000 / 100, tax excluded
        self.assertEqual(self.customer.loyalty_points, 10)
        entry = LoyaltyTransaction.objects.get(customer=self.customer)
        self.assertEqual((entry.kind, entry.points, entry.balance_after), ('EARN', 10, 10))

    def test_points_redeemed_as_discount_before_tax(self):
        self.customer.loyalty_points = 300
        self.customer.save()
        sale = create_sale(user=self.cashier, customer_id=self.customer.pk,
                           items=[{'id': self.item.pk, 'quantity': 1}],
                           tax_percentage='10', amount_paid='1000', redeem_points=200)
        self.assertEqual(sale.discount_amount, Decimal('200.00'))
        self.assertEqual(sale.tax_amount, Decimal('80.00'))
        self.assertEqual(sale.grand_total, Decimal('880.00'))
        self.assertEqual(sale.loyalty_points_earned, 8)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.loyalty_points, 300 - 200 + 8)

    def test_cannot_redeem_more_than_balance(self):
        self.customer.loyalty_points = 5
        self.customer.save()
        with self.assertRaisesMessage(ValidationError, 'only has 5 points'):
            create_sale(user=self.cashier, customer_id=self.customer.pk,
                        items=[{'id': self.item.pk, 'quantity': 1}],
                        amount_paid='2000', redeem_points=6)

    def test_cannot_redeem_more_than_bill(self):
        self.customer.loyalty_points = 5000
        self.customer.save()
        with self.assertRaisesMessage(ValidationError, 'cannot exceed the bill'):
            create_sale(user=self.cashier, customer_id=self.customer.pk,
                        items=[{'id': self.item.pk, 'quantity': 1}],
                        amount_paid='2000', redeem_points=1001)

    @override_settings(LOYALTY={**LOYALTY, 'enabled': False})
    def test_disabled_programme_earns_nothing(self):
        sale = create_sale(user=self.cashier, customer_id=self.customer.pk,
                           items=[{'id': self.item.pk, 'quantity': 1}], amount_paid='2000')
        self.assertEqual(sale.loyalty_points_earned, 0)

    def test_ledger_always_sums_to_balance(self):
        from .loyalty import apply_points
        apply_points(self.customer.pk, 50, LoyaltyTransaction.ADJUST, user=self.cashier, note='Welcome')
        sale = create_sale(user=self.cashier, customer_id=self.customer.pk,
                           items=[{'id': self.item.pk, 'quantity': 2}],
                           amount_paid='5000', redeem_points=50)
        create_sale(user=self.cashier, customer_id=self.customer.pk,
                    items=[{'id': self.item.pk, 'quantity': 1}], amount_paid='5000')
        void_sale(sale, user=self.cashier)
        self.customer.refresh_from_db()
        ledger_sum = sum(LoyaltyTransaction.objects.filter(customer=self.customer).values_list('points', flat=True))
        self.assertEqual(self.customer.loyalty_points, ledger_sum)
        self.assertEqual(self.customer.loyalty_points, 50 + 10)

    def test_balance_never_goes_negative(self):
        from .loyalty import apply_points
        with self.assertRaises(ValidationError):
            apply_points(self.customer.pk, -1, LoyaltyTransaction.ADJUST)


@override_settings(LOYALTY=LOYALTY)
class VoidSaleTests(TestCase):
    def setUp(self):
        self.manager = make_user('manager', role='EX')
        self.customer = make_customer(points=20)
        self.item = make_item('Lamp', quantity=4, price='500.00')
        self.sale = create_sale(user=self.manager, customer_id=self.customer.pk,
                                items=[{'id': self.item.pk, 'quantity': 2}],
                                amount_paid='1000', redeem_points=20)

    def test_void_restores_stock_and_points(self):
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.loyalty_points, 20 - 20 + 9)
        void_sale(self.sale, user=self.manager, reason='Returned')
        self.item.refresh_from_db()
        self.customer.refresh_from_db()
        self.sale.refresh_from_db()
        self.assertEqual(self.item.quantity, 4)
        self.assertEqual(self.customer.loyalty_points, 20)
        self.assertTrue(self.sale.is_voided)
        self.assertEqual(self.sale.voided_by, self.manager)

    def test_cannot_void_twice(self):
        void_sale(self.sale, user=self.manager)
        with self.assertRaises(ValidationError):
            void_sale(self.sale, user=self.manager)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 4)

    def test_void_view_requires_manager(self):
        make_user('op')
        self.client.login(username='op', password=PASSWORD)
        response = self.client.post(reverse('sale-delete', args=[self.sale.pk]), {'reason': 'x'})
        self.assertEqual(response.status_code, 403)

        self.client.login(username='manager', password=PASSWORD)
        response = self.client.post(reverse('sale-delete', args=[self.sale.pk]), {'reason': 'Damaged'})
        self.assertRedirects(response, reverse('sale-detail', args=[self.sale.pk]))
        self.sale.refresh_from_db()
        self.assertTrue(self.sale.is_voided)


@override_settings(LOYALTY=LOYALTY)
class SaleEndpointTests(TestCase):
    def setUp(self):
        self.cashier = make_user('cashier')
        self.customer = make_customer()
        self.item = make_item('Soda', quantity=10, price='50.00')
        self.url = reverse('sale-create')
        self.payload = {
            'customer': self.customer.pk,
            'items': [{'id': self.item.pk, 'quantity': 2}],
            'tax_percentage': 0,
            'amount_paid': '100',
        }

    def post(self, payload, **extra):
        return self.client.post(self.url, json.dumps(payload), content_type='application/json', **extra)

    def test_anonymous_users_cannot_sell(self):
        response = self.post(self.payload)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user-login'), response['Location'])
        self.assertFalse(Sale.objects.exists())

    def test_cashier_can_sell(self):
        self.client.login(username='cashier', password=PASSWORD)
        response = self.post(self.payload)
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['grand_total'], '100.00')
        self.assertTrue(data['receipt_url'].endswith('receipt.pdf'))

    def test_errors_are_reported_without_internals(self):
        self.client.login(username='cashier', password=PASSWORD)
        response = self.post({**self.payload, 'items': [{'id': self.item.pk, 'quantity': 99}]})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Not enough stock', response.json()['message'])

        response = self.client.post(self.url, 'not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_csrf_is_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.login(username='cashier', password=PASSWORD)
        response = client.post(self.url, json.dumps(self.payload), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_sale_detail_shows_summary_not_receipt(self):
        self.client.login(username='cashier', password=PASSWORD)
        sale_id = self.post(self.payload).json()['sale_id']
        response = self.client.get(reverse('sale-detail', args=[sale_id]))
        self.assertContains(response, 'Print receipt')
        self.assertContains(response, reverse('sale-receipt', args=[sale_id]))
        self.assertNotContains(response, 'THANK YOU')
        self.assertNotContains(response, 'code-barre')

    @skipUnless(weasyprint_available(), 'WeasyPrint system libraries not installed')
    def test_receipt_pdf_inline_and_download(self):
        self.client.login(username='cashier', password=PASSWORD)
        sale_id = self.post(self.payload).json()['sale_id']
        url = reverse('sale-receipt', args=[sale_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertTrue(response['Content-Disposition'].startswith('inline'))
        response = self.client.get(url + '?download=1')
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))

    def test_receipt_requires_login(self):
        sale = create_sale(user=self.cashier, customer_id=self.customer.pk,
                           items=[{'id': self.item.pk, 'quantity': 1}], amount_paid='50')
        response = self.client.get(reverse('sale-receipt', args=[sale.pk]))
        self.assertEqual(response.status_code, 302)


class PurchaseStockTests(TestCase):
    def setUp(self):
        self.vendor = make_vendor()
        self.item = make_item('Rice', quantity=10, price='100.00')

    def stock(self):
        return Item.objects.get(pk=self.item.pk).quantity

    def test_pending_purchase_does_not_add_stock(self):
        Purchase.objects.create(item=self.item, vendor=self.vendor, quantity=5, price=Decimal('80'))
        self.assertEqual(self.stock(), 10)

    def test_received_purchase_adds_stock_once(self):
        purchase = Purchase.objects.create(item=self.item, vendor=self.vendor, quantity=5,
                                           price=Decimal('80'), delivery_status='S')
        self.assertEqual(self.stock(), 15)
        purchase.description = 'edited'
        purchase.save()
        self.assertEqual(self.stock(), 15)
        self.assertEqual(purchase.total_value, Decimal('400'))

    def test_marking_received_then_changing_quantity(self):
        purchase = Purchase.objects.create(item=self.item, vendor=self.vendor, quantity=5, price=Decimal('80'))
        purchase.delivery_status = 'S'
        purchase.save()
        self.assertEqual(self.stock(), 15)
        purchase.quantity = 3
        purchase.save()
        self.assertEqual(self.stock(), 13)

    def test_changing_item_moves_stock(self):
        other = make_item('Beans', quantity=0, price='90.00')
        purchase = Purchase.objects.create(item=self.item, vendor=self.vendor, quantity=4,
                                           price=Decimal('80'), delivery_status='S')
        purchase.item = other
        purchase.save()
        self.assertEqual(self.stock(), 10)
        self.assertEqual(Item.objects.get(pk=other.pk).quantity, 4)

    def test_delete_removes_received_stock(self):
        purchase = Purchase.objects.create(item=self.item, vendor=self.vendor, quantity=4,
                                           price=Decimal('80'), delivery_status='S')
        purchase.delete()
        self.assertEqual(self.stock(), 10)

    def test_cannot_remove_stock_that_was_sold(self):
        purchase = Purchase.objects.create(item=self.item, vendor=self.vendor, quantity=4,
                                           price=Decimal('80'), delivery_status='S')
        Item.objects.filter(pk=self.item.pk).update(quantity=1)
        with self.assertRaises(ValidationError):
            purchase.delete()
        self.assertTrue(Purchase.objects.filter(pk=purchase.pk).exists())


class ExportTests(TestCase):
    def test_exports_are_for_managers(self):
        make_user('op')
        make_user('boss', role='EX')
        purchase_item = make_item()
        Purchase.objects.create(item=purchase_item, vendor=make_vendor(), quantity=1, price=Decimal('1'))
        self.client.login(username='op', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('sales-export')).status_code, 403)
        self.client.login(username='boss', password=PASSWORD)
        for name in ('sales-export', 'purchases-export'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertIn('spreadsheetml', response['Content-Type'])
