from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='user-register'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('logout/', auth_views.LogoutView.as_view(), name='user-logout'),
    path('password/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password/done/',
    ), name='password-change'),
    path('password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html',
    ), name='password-change-done'),
    path('profile/', views.profile, name='user-profile'),
    path('profile/update/', views.profile_update, name='user-profile-update'),

    # Staff
    path('profiles/', views.ProfileListView.as_view(), name='profile_list'),
    path('new-profile/', views.ProfileCreateView.as_view(), name='profile-create'),
    path('profile/<int:pk>/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/<int:pk>/approve/', views.profile_approve, name='profile-approve'),
    path('profile/<int:pk>/delete/', views.ProfileDeleteView.as_view(), name='profile-delete'),

    # Customers
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/update/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('customers/<int:pk>/loyalty/', views.customer_loyalty_adjust, name='customer_loyalty_adjust'),
    path('get_customers/', views.get_customers, name='get_customers'),

    # Vendors
    path('vendors/', views.VendorListView.as_view(), name='vendor-list'),
    path('vendors/new/', views.VendorCreateView.as_view(), name='vendor-create'),
    path('vendors/<int:pk>/update/', views.VendorUpdateView.as_view(), name='vendor-update'),
    path('vendors/<int:pk>/delete/', views.VendorDeleteView.as_view(), name='vendor-delete'),
]
