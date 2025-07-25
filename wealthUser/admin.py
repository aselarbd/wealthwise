from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Group, GroupInviteLink

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'group', 'is_admin', 'is_staff', 'is_active']
    list_filter = ['group', 'is_admin', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    
    # Add custom fields to the user edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('group', 'is_admin')}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers can see all users
        elif hasattr(request.user, 'is_admin') and request.user.is_admin:
            return qs  # Admin users can see all users
        else:
            # Regular users can only see users in their group
            return qs.filter(group=request.user.group)

@admin.register(GroupInviteLink)
class GroupInviteLinkAdmin(admin.ModelAdmin):
    list_display = ['group', 'token', 'is_used', 'created_by', 'created_at']
    list_filter = ['is_used', 'group']
    search_fields = ['group__name', 'created_by__username']
    readonly_fields = ['token', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers can see all invite links
        elif hasattr(request.user, 'is_admin') and request.user.is_admin:
            return qs  # Admin users can see all invite links
        else:
            # Regular users can only see invite links for their group
            return qs.filter(group=request.user.group)
