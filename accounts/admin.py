from django.contrib import admin

from .models import Customer, Profile, Vendor


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telephone', 'email', 'role', 'status')
    list_filter = ('role', 'status')
    list_editable = ('role', 'status')
    search_fields = ('user__username', 'email', 'first_name', 'last_name')
    list_select_related = ('user',)


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
