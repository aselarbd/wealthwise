from django.contrib import admin
from .models import NetWorthItem


@admin.register(NetWorthItem)
class NetWorthItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_type', 'asset_category', 'value', 'group', 'created_at']
    list_filter = ['item_type', 'asset_category', 'group', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'value')
        }),
        ('Classification', {
            'fields': ('item_type', 'asset_category', 'group')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers can see all items
        elif hasattr(request.user, 'is_admin') and request.user.is_admin:
            return qs  # Admin users can see all items
        else:
            # Regular users can only see items from their group
            return qs.filter(group=request.user.group)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "group":
            if not request.user.is_superuser:
                # Non-superusers can only assign to their own group
                kwargs["queryset"] = kwargs["queryset"].filter(id=request.user.group.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
