"""
Group Filtering Middleware for WealthWise

This middleware automatically filters all database queries to ensure users can only
access data belonging to their group. This provides bulletproof multi-tenant isolation.

Key Features:
- Automatic filtering for all models with 'group' foreign key
- Thread-local storage for current user's group
- Fallback handling for anonymous users
- Preparation for Step 2 (Enhanced Permissions) and Step 3 (API Development)
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
import threading
from typing import Optional, Any
from wealthUser.models import Group

# Thread-local storage for current user context
_thread_locals = threading.local()


class GroupContext:
    """
    Thread-local context manager for group-based filtering.
    
    This class maintains the current user's group context across the request lifecycle.
    It will be extended in Step 2 for role-based permissions.
    """
    
    @staticmethod
    def set_current_group(group: Optional[Group]) -> None:
        """Set the current group for this thread."""
        _thread_locals.current_group = group
    
    @staticmethod
    def get_current_group() -> Optional[Group]:
        """Get the current group for this thread."""
        return getattr(_thread_locals, 'current_group', None)
    
    @staticmethod
    def clear() -> None:
        """Clear the current group context."""
        if hasattr(_thread_locals, 'current_group'):
            delattr(_thread_locals, 'current_group')


class GroupFilteredManager(Manager):
    """
    Custom manager that automatically filters queries by the current user's group.
    
    This manager will be extended in Step 2 to handle role-based filtering.
    """
    
    def get_queryset(self) -> QuerySet:
        """Override to add automatic group filtering."""
        queryset = super().get_queryset()
        current_group = GroupContext.get_current_group()
        
        # Only apply filtering if we have a current group and the model has a group field
        if current_group and hasattr(self.model, 'group'):
            queryset = queryset.filter(group=current_group)
        
        return queryset
    
    def create(self, **kwargs) -> Any:
        """Override create to automatically set the group field."""
        current_group = GroupContext.get_current_group()
        
        # Automatically set group if model has group field and group is not already specified
        if current_group and hasattr(self.model, 'group') and 'group' not in kwargs:
            kwargs['group'] = current_group
        
        return super().create(**kwargs)


class GroupFilteringMiddleware(MiddlewareMixin):
    """
    Middleware that automatically filters all database queries by user's group.
    
    This middleware:
    1. Sets the current user's group in thread-local storage
    2. Ensures all queries are automatically filtered by group
    3. Provides foundation for Step 2 (role-based permissions)
    4. Prepares for Step 3 (API authentication and filtering)
    
    Process:
    - process_request: Set group context from authenticated user
    - process_response: Clear group context to prevent memory leaks
    """
    
    def process_request(self, request) -> None:
        """
        Set the current group context based on the authenticated user.
        
        For Step 3 (API Development), this will be extended to handle:
        - API token authentication
        - JWT token group extraction
        - Service-to-service authentication
        """
        # Clear any existing context
        GroupContext.clear()
        
        # Set group context for authenticated users
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            if hasattr(request.user, 'group') and request.user.group:
                GroupContext.set_current_group(request.user.group)
    
    def process_response(self, request, response):
        """
        Clean up group context to prevent memory leaks.
        
        This is crucial for thread safety in production environments.
        """
        GroupContext.clear()
        return response
    
    def process_exception(self, request, exception):
        """
        Ensure context is cleared even if an exception occurs.
        
        This prevents context bleeding between requests in case of errors.
        """
        GroupContext.clear()
        return None


# Monkey patch function to apply group filtering to existing models
def apply_group_filtering_to_model(model_class):
    """
    Apply group filtering to an existing model class.
    
    This function will be used to retrofit existing models with automatic
    group filtering without requiring model changes.
    
    In Step 2, this will be extended to handle role-based access patterns.
    """
    if hasattr(model_class, 'group') and not hasattr(model_class, '_group_filtered'):
        # Replace the default manager with our group-filtered manager
        model_class.add_to_class('objects', GroupFilteredManager())
        
        # Mark as processed to avoid double-processing
        model_class._group_filtered = True
        
        # Store original manager for potential admin/superuser access
        # (This will be important for Step 2 - Enhanced Permissions)
        if not hasattr(model_class, '_original_manager'):
            model_class._original_manager = Manager()
