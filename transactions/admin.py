from django.contrib import admin

from .models import Sale, SaleDetail, Purchase, LoyaltyTransaction


class SaleDetailInline(admin.TabularInline):
    model = SaleDetail
    extra = 0
    can_delete = False
    readonly_fields = ('item', 'price', 'quantity', 'total_detail')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """
    Sales are read only here. They are created at the till and voided from
    the app so stock and loyalty points always stay in step.
    """
    list_display = (
        'receipt_number', 'customer', 'date_added', 'grand_total',
        'amount_paid', 'status', 'served_by',
    )
    search_fields = ('customer__first_name', 'customer__last_name', 'id')
    list_filter = ('status', 'date_added')
    list_select_related = ('customer', 'served_by')
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    inlines = [SaleDetailInline]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'customer', 'kind', 'points', 'balance_after', 'sale', 'created_by')
    list_filter = ('kind',)
    search_fields = ('customer__first_name', 'customer__last_name', 'note')
    list_select_related = ('customer', 'sale', 'created_by')

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'item', 'vendor', 'order_date', 'delivery_date',
        'quantity', 'price', 'total_value', 'delivery_status',
    )
    search_fields = ('item__name', 'vendor__name', 'slug')
    list_filter = ('order_date', 'vendor', 'delivery_status')
    list_select_related = ('item', 'vendor')
    ordering = ('-order_date',)
    readonly_fields = ('total_value', 'stock_applied')
