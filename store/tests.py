from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from InventoryMS.test_utils import make_customer, make_item, make_user, make_vendor
from transactions.services import create_sale

from .models import Category, Delivery, Item


class StockTests(TestCase):
    def test_adjust_stock_never_goes_negative(self):
        from django.core.exceptions import ValidationError
        item = make_item(quantity=2)
        Item.adjust_stock(item.pk, -2)
        with self.assertRaises(ValidationError):
            Item.adjust_stock(item.pk, -1)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 0)

    def test_price_is_decimal(self):
        item = make_item(price='0.10')
        item.refresh_from_db()
        self.assertEqual(item.price * 3, Decimal('0.30'))


class PageTests(TestCase):
    """Every page renders for an admin, with data and when empty."""

    def setUp(self):
        self.admin = make_user('admin', superuser=True)
        self.client.force_login(self.admin)

    def pages(self):
        item = Item.objects.first()
        category = Category.objects.first()
        delivery = Delivery.objects.first()
        names = [
            'dashboard', 'productslist', 'product-create', 'category-list', 'category-create',
            'deliveries', 'delivery-create', 'saleslist', 'sale-create', 'purchaseslist',
            'purchase-create', 'customer_list', 'customer_create', 'vendor-list', 'vendor-create',
            'invoicelist', 'invoice-create', 'bill_list', 'bill_create', 'profile_list',
            'profile-create', 'user-profile', 'user-profile-update', 'password-change',
        ]
        urls = [reverse(n) for n in names]
        if item:
            urls += [reverse('product-detail', args=[item.slug]),
                     reverse('product-update', args=[item.slug]),
                     reverse('product-delete', args=[item.slug])]
        if category:
            urls += [reverse('category-detail', args=[category.pk])]
        if delivery:
            urls += [reverse('delivery-detail', args=[delivery.pk]),
                     reverse('delivery-delete', args=[delivery.pk])]
        return urls

    def test_pages_render_empty(self):
        for url in self.pages():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_pages_render_with_data(self):
        from django.utils import timezone
        vendor = make_vendor()
        item = make_item(vendor=vendor)
        make_item('Empty shelf', quantity=0)
        Delivery.objects.create(item=item, customer_name='Joe', date=timezone.now())
        create_sale(user=self.admin, customer_id=make_customer().pk,
                    items=[{'id': item.pk, 'quantity': 1}], amount_paid='100')
        for url in self.pages():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Out of stock')

    def test_search_keeps_query_in_pagination(self):
        for n in range(25):
            make_item(f'Cola {n:02d}')
        response = self.client.get(reverse('productslist'), {'q': 'cola'})
        self.assertContains(response, 'q=cola&amp;page=2')

    def test_chart_data_is_not_injected_as_html(self):
        Category.objects.create(name='</script><script>alert(1)</script>')
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, '</script><script>alert(1)')


class DeleteProtectionTests(TestCase):
    def test_product_with_sales_shows_message_instead_of_error(self):
        manager = make_user('mgr', role='EX')
        item = make_item()
        create_sale(user=manager, customer_id=make_customer().pk,
                    items=[{'id': item.pk, 'quantity': 1}], amount_paid='100')
        self.client.force_login(manager)
        response = self.client.post(reverse('product-delete', args=[item.slug]), follow=True)
        self.assertContains(response, 'cannot be deleted')
        self.assertTrue(Item.objects.filter(pk=item.pk).exists())

    def test_category_with_products_is_protected(self):
        manager = make_user('mgr', role='EX')
        item = make_item()
        self.client.force_login(manager)
        response = self.client.post(reverse('category-delete', args=[item.category.pk]), follow=True)
        self.assertContains(response, 'still has products')


class ItemSearchTests(TestCase):
    def test_lists_only_in_stock_items(self):
        make_item('Milk', quantity=3)
        make_item('Milkshake', quantity=0)
        self.client.force_login(make_user('op'))
        data = self.client.get(reverse('get_items'), {'term': 'milk'}).json()
        self.assertEqual([d['name'] for d in data], ['Milk'])
        self.assertEqual(data[0]['stock'], 3)

    def test_requires_login_and_get(self):
        self.assertEqual(self.client.get(reverse('get_items')).status_code, 302)
        self.client.force_login(make_user('op'))
        self.assertEqual(self.client.post(reverse('get_items')).status_code, 405)


class SecurityHeaderTests(TestCase):
    def test_html_pages_get_a_strict_policy(self):
        response = self.client.get(reverse('user-login'))
        csp = response.headers['Content-Security-Policy']
        self.assertNotIn('unsafe-inline', csp)
        self.assertNotIn('unsafe-eval', csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn('camera=()', response.headers['Permissions-Policy'])
        self.assertEqual(response.headers['Cross-Origin-Resource-Policy'], 'same-origin')

    def test_csrf_cookie_is_http_only(self):
        response = self.client.get(reverse('user-login'))
        self.assertTrue(response.cookies['csrftoken']['httponly'])

    def test_pages_have_no_inline_scripts_or_styles(self):
        self.client.force_login(make_user('headers', role='AD'))
        for name in ('dashboard', 'sale-create', 'user-profile'):
            content = self.client.get(reverse(name)).content.decode()
            self.assertNotIn('<script>', content, name)
            self.assertNotIn('<style', content, name)
            self.assertNotIn('style="', content, name)
