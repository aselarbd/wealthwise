"""
Permission Decorators for WealthWise - Step 2: Enhanced Permissions

This module provides decorators for role-based access control within groups.
These decorators work with the GroupContext middleware to enforce permissions.

Key Features:
- Role-based permission checking
- Easy-to-use decorators for views
- Integration with existing group filtering
- Preparation for Step 3 (API permissions)
"""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from typing import Callable, Any
from .middleware import GroupContext


def require_permission(permission: str):
    """
    Decorator that requires a specific permission within the user's group.
    
    Usage:
        @require_permission('create')
        def create_asset(request):
            # User must have 'create' permission
            pass
    
    Args:
        permission: Required permission ('read', 'create', 'update', 'delete', 'manage_users')
    
    Returns:
        403 Forbidden if user lacks permission
        Original view response if permission granted
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user has the required permission
            if not GroupContext.has_permission(permission):
                return JsonResponse({
                    'error': 'Permission denied',
                    'required_permission': permission,
                    'message': f'You need {permission} permission to perform this action'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_group_membership(view_func: Callable) -> Callable:
    """
    Decorator that requires user to be a member of a group.
    
    This is a base requirement - user must have a group before any permissions apply.
    
    Usage:
        @require_group_membership
        def some_view(request):
            # User must belong to a group
            pass
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        current_group = GroupContext.get_current_group()
        if not current_group:
            return JsonResponse({
                'error': 'Group membership required',
                'message': 'You must be assigned to a group to access this resource'
            }, status=400)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class PermissionRequiredMixin:
    """
    Mixin for class-based views that require specific permissions.
    
    Usage:
        class AssetCreateView(PermissionRequiredMixin, View):
            required_permission = 'create'
            
            def post(self, request):
                # User automatically has 'create' permission
                pass
    """
    required_permission = None
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to check permissions before calling view methods."""
        if self.required_permission:
            if not GroupContext.has_permission(self.required_permission):
                return JsonResponse({
                    'error': 'Permission denied',
                    'required_permission': self.required_permission,
                    'message': f'You need {self.required_permission} permission to perform this action'
                }, status=403)
        
        return super().dispatch(request, *args, **kwargs)


# Convenience decorators for common permission combinations
def require_read_permission(view_func: Callable) -> Callable:
    """Shortcut decorator for read permission."""
    return require_permission('read')(view_func)


def require_create_permission(view_func: Callable) -> Callable:
    """Shortcut decorator for create permission."""
    return require_permission('create')(view_func)


def require_update_permission(view_func: Callable) -> Callable:
    """Shortcut decorator for update permission."""
    return require_permission('update')(view_func)


def require_delete_permission(view_func: Callable) -> Callable:
    """Shortcut decorator for delete permission."""
    return require_permission('delete')(view_func)


def require_admin_permission(view_func: Callable) -> Callable:
    """Shortcut decorator for admin-level permissions (manage_users)."""
    return require_permission('manage_users')(view_func)


# Method decorators for class-based views
def method_permission_required(permission: str):
    """
    Method decorator for class-based views.
    
    Usage:
        class AssetView(View):
            @method_permission_required('create')
            def post(self, request):
                # Requires create permission
                pass
            
            @method_permission_required('delete')
            def delete(self, request, asset_id):
                # Requires delete permission
                pass
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def _wrapped_method(self, request, *args, **kwargs):
            if not GroupContext.has_permission(permission):
                return JsonResponse({
                    'error': 'Permission denied',
                    'required_permission': permission,
                    'message': f'You need {permission} permission to perform this action'
                }, status=403)
            
            return method(self, request, *args, **kwargs)
        return _wrapped_method
    return decorator


# Combined decorators for convenience
def login_and_permission_required(permission: str):
    """
    Combined decorator that requires both login and specific permission.
    
    Usage:
        @login_and_permission_required('create')
        def create_asset(request):
            # User must be logged in AND have create permission
            pass
    """
    def decorator(view_func: Callable) -> Callable:
        # Apply login_required first, then permission check
        @login_required
        @require_permission(permission)
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
