from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views

from accounts import views as user_views
from .views import (
    ProfileListView,
    ProfileCreateView,
    ProfileUpdateView,
    ProfileDeleteView,
    CustomerListView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDeleteView,
    get_customers
)

urlpatterns = [
    path('register/', user_views.register, name='user-register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html'), name='user-login'),
    path('profile/', user_views.profile, name='user-profile'),
    path('profile/update/', user_views.profile_update,
         name='user-profile-update'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='accounts/logout.html'), name='user-logout'),
    path('profiles/', ProfileListView.as_view(), name='profile_list'),
    path('new-profile/', ProfileCreateView.as_view(), name='profile-create'),
    path('profile/<int:pk>/update/', ProfileUpdateView.as_view(),
         name='profile-update'),
    path('profile/<int:pk>/delete/', ProfileDeleteView.as_view(),
         name='profile-delete'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', CustomerCreateView.as_view(),
         name='customer_create'),
    path('customers/<int:pk>/update/', CustomerUpdateView.as_view(),
         name='customer_update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(),
         name='customer_delete'),
    path('get_customers/', get_customers, name='get_customers'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
