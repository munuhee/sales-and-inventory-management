from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/',ProductListView.as_view(), name="productslist"),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('new-product/', ProductCreateView.as_view(), name='product-create'),
    path('product/<slug:slug>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('product/<slug:slug>/delete/', ProductDeleteView.as_view(), name='product-delete'),

]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)