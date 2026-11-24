from django.urls import path

from . import views

urlpatterns = [
    path('invoices/', views.InvoiceListView.as_view(), name='invoicelist'),
    path('invoice/<slug:slug>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoice/<slug:slug>/pdf/', views.invoice_pdf, name='invoice-pdf'),
    path('new-invoice/', views.InvoiceCreateView.as_view(), name='invoice-create'),
    path('invoice/<slug:slug>/update/', views.InvoiceUpdateView.as_view(), name='invoice-update'),
    path('invoice/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice-delete'),
]
