from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from django.contrib.auth import views as auth_views
from accounts import views as user_views
from django.conf.urls.static import static
from .views import (
    ProfileListView,
    #ProfileDetailView,
    ProfileCreateView,
    ProfileUpdateView,
    ProfileDeleteView,
)
urlpatterns = [
    path('register/', user_views.register, name='user-register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html'), name='user-login'),
    path('profile/', user_views.profile, name='user-profile'),
    path('profile/update/', user_views.profile_update,
         name='user-profile-update'),
    path('logout/', auth_views.LogoutView.as_view(template_name='accounts/logout.html'),
         name='user-logout'),
    path('profiles/',ProfileListView.as_view(), name="profile_list"),
    #path('profile/<slug:slug>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('new-profile/', ProfileCreateView.as_view(), name='profile-create'),
    path('profile/<int:pk>/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/<int:pk>/update/', ProfileDeleteView.as_view(), name='profile-delete')
]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)