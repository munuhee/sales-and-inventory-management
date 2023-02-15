from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from .views import (
    PurchaseListView,
    PurchaseDetailView,
    PurchaseCreateView,
    PurchaseUpdateView,
    PurchaseDeleteView,
    SaleListView,
    SaleDetailView,
    SaleCreateView,
    SaleUpdateView,
    SaleDeleteView,
)

urlpatterns = [
    path('purchases/', PurchaseListView.as_view(), name="purchaseslist"),
    path('purchase/<slug:slug>/', PurchaseDetailView.as_view(), name='purchase-detail'),
    path('new-purchase/', PurchaseCreateView.as_view(), name='purchase-create'),
    path('purchase/<int:pk>/update/', PurchaseUpdateView.as_view(), name='purchase-update'),
    path('purchase/<int:pk>/delete/', PurchaseDeleteView.as_view(), name='purchase-delete'),
    path('sales/',SaleListView.as_view(), name="saleslist"),
    path('sale/<int:pk>/', SaleDetailView.as_view(), name='sale-detail'),
    path('new-sale/', SaleCreateView.as_view(), name='sale-create'),
    path('sale/<slug:slug>/update/', SaleUpdateView.as_view(), name='sale-update'),
    path('sale/<slug:slug>/delete/', SaleDeleteView.as_view(), name='sale-delete'),

]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)