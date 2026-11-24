from django.urls import path

from . import views

urlpatterns = [
    # Purchases
    path('purchases/', views.PurchaseListView.as_view(), name='purchaseslist'),
    path('purchase/<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase-detail'),
    path('new-purchase/', views.PurchaseCreateView.as_view(), name='purchase-create'),
    path('purchase/<int:pk>/update/', views.PurchaseUpdateView.as_view(), name='purchase-update'),
    path('purchase/<int:pk>/delete/', views.PurchaseDeleteView.as_view(), name='purchase-delete'),

    # Sales
    path('sales/', views.SaleListView.as_view(), name='saleslist'),
    path('sale/<int:pk>/', views.SaleDetailView.as_view(), name='sale-detail'),
    path('sale/<int:pk>/receipt.pdf', views.sale_receipt_pdf, name='sale-receipt'),
    path('sale/<int:pk>/void/', views.SaleVoidView.as_view(), name='sale-delete'),
    path('new-sale/', views.sale_create_view, name='sale-create'),

    # Exports
    path('sales/export/', views.export_sales_to_excel, name='sales-export'),
    path('purchases/export/', views.export_purchases_to_excel, name='purchases-export'),
]
