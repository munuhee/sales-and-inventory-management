from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from InventoryMS.test_utils import PASSWORD, make_customer, make_user
from transactions.models import LoyaltyTransaction

from .models import Customer


class RegistrationAndLoginTests(TestCase):
    def setUp(self):
        cache.clear()

    def login(self, username, password=PASSWORD):
        return self.client.post(reverse('user-login'), {'username': username, 'password': password})

    def test_self_signup_waits_for_approval(self):
        response = self.client.post(reverse('user-register'), {
            'username': 'newbie', 'email': 'newbie@example.com',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('user-login'))
        user = User.objects.get(username='newbie')
        self.assertEqual(user.profile.status, 'PEN')

        response = self.login('newbie')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'awaiting approval')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_admin_approves_signup(self):
        make_user('admin', superuser=True)
        pending = make_user('pending', status='PEN')
        self.client.login(username='admin', password=PASSWORD)
        self.client.post(reverse('profile-approve', args=[pending.profile.pk]))
        self.client.logout()
        response = self.login('pending')
        self.assertRedirects(response, reverse('dashboard'))

    def test_duplicate_email_rejected(self):
        make_user('taken')
        response = self.client.post(reverse('user-register'), {
            'username': 'other', 'email': 'TAKEN@example.com',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertContains(response, 'already exists')

    @override_settings(ALLOW_REGISTRATION=False)
    def test_registration_can_be_disabled(self):
        self.assertEqual(self.client.get(reverse('user-register')).status_code, 404)

    @override_settings(LOGIN_MAX_ATTEMPTS=3)
    def test_login_is_throttled(self):
        make_user('victim')
        for _ in range(3):
            self.login('victim', 'wrong')
        response = self.login('victim')  # correct password, but locked
        self.assertContains(response, 'Too many failed attempts')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_deactivated_user_is_signed_out(self):
        user = make_user('leaver')
        self.client.login(username='leaver', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        user.profile.status = 'OL'
        user.profile.save()
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('user-login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post(self):
        make_user('someone')
        self.client.login(username='someone', password=PASSWORD)
        response = self.client.post(reverse('user-logout'))
        self.assertRedirects(response, reverse('user-login'))


class RoleAccessTests(TestCase):
    """The permission matrix, page by page."""

    MATRIX = [
        # (url name, args, minimum role)
        ('dashboard', [], 'OP'),
        ('productslist', [], 'OP'),
        ('sale-create', [], 'OP'),
        ('saleslist', [], 'OP'),
        ('customer_list', [], 'OP'),
        ('customer_create', [], 'OP'),
        ('deliveries', [], 'OP'),
        ('invoicelist', [], 'OP'),
        ('category-list', [], 'OP'),
        ('product-create', [], 'EX'),
        ('category-create', [], 'EX'),
        ('purchaseslist', [], 'EX'),
        ('purchase-create', [], 'EX'),
        ('vendor-list', [], 'EX'),
        ('bill_list', [], 'EX'),
        ('invoice-create', [], 'EX'),
        ('sales-export', [], 'EX'),
        ('profile_list', [], 'AD'),
        ('profile-create', [], 'AD'),
    ]
    LEVEL = {'OP': 1, 'EX': 2, 'AD': 3}

    def setUp(self):
        self.users = {
            'OP': make_user('operative', role='OP'),
            'EX': make_user('executive', role='EX'),
            'AD': make_user('admin', role='AD'),
        }

    def test_anonymous_is_sent_to_login(self):
        for name, args, _ in self.MATRIX:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('user-login'), response['Location'])

    def test_each_role_gets_exactly_its_pages(self):
        for role, user in self.users.items():
            self.client.force_login(user)
            for name, args, minimum in self.MATRIX:
                with self.subTest(role=role, page=name):
                    status = self.client.get(reverse(name, args=args)).status_code
                    expected = 200 if self.LEVEL[role] >= self.LEVEL[minimum] else 403
                    self.assertEqual(status, expected)

    def test_export_via_querystring_is_blocked_for_operatives(self):
        self.client.force_login(self.users['OP'])
        response = self.client.get(reverse('productslist') + '?_export=xlsx')
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.users['EX'])
        response = self.client.get(reverse('productslist') + '?_export=xlsx')
        self.assertEqual(response.status_code, 200)

    def test_operative_nav_hides_manager_sections(self):
        self.client.force_login(self.users['OP'])
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, reverse('purchaseslist'))
        self.assertNotContains(response, reverse('profile_list'))


class StaffManagementTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin', role='AD')
        self.client.force_login(self.admin)

    def test_admin_creates_active_staff_with_role(self):
        response = self.client.post(reverse('profile-create'), {
            'username': 'till2', 'email': 'till2@example.com', 'first_name': 'Till', 'last_name': 'Two',
            'password1': PASSWORD, 'password2': PASSWORD, 'role': 'OP', 'status': 'A',
        })
        self.assertRedirects(response, reverse('profile_list'))
        user = User.objects.get(username='till2')
        self.assertEqual((user.profile.role, user.profile.status), ('OP', 'A'))

    def test_admin_cannot_lock_themselves_out(self):
        response = self.client.post(reverse('profile-update', args=[self.admin.profile.pk]), {
            'first_name': '', 'last_name': '', 'telephone': '', 'email': '',
            'role': 'OP', 'status': 'A',
        })
        # Only a superuser may change an Admin account, including your own.
        self.assertEqual(response.status_code, 403)
        self.admin.profile.refresh_from_db()
        self.assertEqual(self.admin.profile.role, 'AD')

    def test_admin_cannot_delete_self(self):
        response = self.client.post(reverse('profile-delete', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_touch_superuser(self):
        root = make_user('root', superuser=True)
        response = self.client.post(reverse('profile-delete', args=[root.profile.pk]))
        self.assertEqual(response.status_code, 403)

    def test_delete_removes_user(self):
        target = make_user('gone')
        self.client.post(reverse('profile-delete', args=[target.profile.pk]))
        self.assertFalse(User.objects.filter(username='gone').exists())

    def test_superuser_profile_is_admin_and_active(self):
        root = make_user('root2', superuser=True)
        self.assertEqual((root.profile.role, root.profile.status), ('AD', 'A'))


class CustomerLoyaltyTests(TestCase):
    def setUp(self):
        self.customer = make_customer(points=10)

    def test_points_cannot_be_typed_into_customer_form(self):
        self.client.force_login(make_user('op'))
        self.client.post(reverse('customer_update', args=[self.customer.pk]), {
            'first_name': 'Jane', 'last_name': 'Doe', 'loyalty_points': 99999,
        })
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.loyalty_points, 10)

    def test_manager_adjustment_is_recorded(self):
        manager = make_user('mgr', role='EX')
        self.client.force_login(manager)
        response = self.client.post(reverse('customer_loyalty_adjust', args=[self.customer.pk]),
                                    {'points': '-4', 'note': 'Correction'})
        self.assertRedirects(response, reverse('customer_detail', args=[self.customer.pk]))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.loyalty_points, 6)
        entry = LoyaltyTransaction.objects.get(customer=self.customer)
        self.assertEqual((entry.kind, entry.points, entry.created_by), ('ADJUST', -4, manager))

    def test_operative_cannot_adjust(self):
        self.client.force_login(make_user('op'))
        response = self.client.post(reverse('customer_loyalty_adjust', args=[self.customer.pk]),
                                    {'points': '100', 'note': 'x'})
        self.assertEqual(response.status_code, 403)

    def test_adjustment_cannot_go_negative(self):
        self.client.force_login(make_user('mgr', role='EX'))
        self.client.post(reverse('customer_loyalty_adjust', args=[self.customer.pk]),
                         {'points': '-11', 'note': 'x'})
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.loyalty_points, 10)

    def test_customer_search_and_str(self):
        Customer.objects.create(first_name='Solo')  # no last name: used to crash
        self.assertEqual(str(Customer.objects.get(first_name='Solo')), 'Solo')
        self.client.force_login(make_user('op'))
        data = self.client.get(reverse('get_customers'), {'term': 'jan'}).json()
        self.assertEqual([r['text'] for r in data['results']], ['Jane Doe'])
        self.assertEqual(data['results'][0]['loyalty_points'], 10)

    def test_customer_with_sales_cannot_be_deleted(self):
        from InventoryMS.test_utils import make_item
        from transactions.services import create_sale
        cashier = make_user('op')
        create_sale(user=cashier, customer_id=self.customer.pk,
                    items=[{'id': make_item().pk, 'quantity': 1}], amount_paid='100')
        self.client.force_login(make_user('mgr', role='EX'))
        response = self.client.post(reverse('customer_delete', args=[self.customer.pk]), follow=True)
        self.assertContains(response, 'cannot be deleted')
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())
