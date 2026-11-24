from django.contrib import admin

from .models import Customer, Profile, StaffAuditLog, Vendor


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telephone', 'email', 'role', 'status')
    list_filter = ('role', 'status')
    search_fields = ('user__username', 'email', 'first_name', 'last_name')
    list_select_related = ('user',)
    fields = ('user', 'role', 'status', 'first_name', 'last_name', 'telephone', 'email')
    readonly_fields = ('user', 'role', 'status')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StaffAuditLog)
class StaffAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'actor_username', 'action', 'target_username',
        'previous_role', 'new_role', 'previous_status', 'new_status',
        'previous_login_enabled', 'new_login_enabled',
    )
    list_filter = ('action', 'created_at')
    search_fields = ('actor_username', 'target_username')
    readonly_fields = (
        'actor', 'actor_username', 'target_user', 'target_username', 'action',
        'previous_role', 'new_role', 'previous_status', 'new_status', 'created_at',
        'previous_login_enabled', 'new_login_enabled',
    )
    ordering = ('-created_at', '-pk')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'email', 'loyalty_points')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    # Points change only through sales or recorded adjustments.
    readonly_fields = ('loyalty_points',)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    fields = ('name', 'phone_number', 'address')
    list_display = ('name', 'phone_number', 'address')
    search_fields = ('name', 'phone_number', 'address')
