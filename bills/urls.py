from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from .views import (
    BillListView,
    #BillDetailView,
    BillCreateView,
    BillUpdateView,
    BillDeleteView,
)

urlpatterns = [
    path('bills/',BillListView.as_view(), name="bill_list"),
    #path('bill/<slug:slug>/', BillDetailView.as_view(), name='bill-detail'),
    path('new-bill/', BillCreateView.as_view(), name='bill-create'),
    path('bill/<slug:slug>/update/', BillUpdateView.as_view(), name='bill-update'),
    path('bill/<int:id>/delete/', BillDeleteView.as_view(), name='bill-delete'),
]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)