from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Group(TimeStampedModel):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name


class GroupScopedModel(models.Model):
    group = models.ForeignKey("Group", on_delete=models.CASCADE)

    class Meta:
        abstract = True


class CustomUser(AbstractUser):
    """
    Enhanced User model with role-based permissions within groups.
    
    Roles define what actions a user can perform within their group:
    - ADMIN: Full CRUD access, can manage group members and settings
    - EDITOR: Can create, read, and update data, cannot delete or manage users
    - VIEWER: Read-only access to group data
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'
    
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text="User's role within their group"
    )
    # Keep is_admin for backward compatibility and system-wide admin access
    is_admin = models.BooleanField(
        default=False, 
        help_text="System-wide admin (overrides group role)"
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()}) - {self.group.name if self.group else 'No Group'}"
    
    def has_group_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission within their group.
        
        Permission levels:
        - 'read': Can view data
        - 'create': Can create new data
        - 'update': Can modify existing data
        - 'delete': Can delete data
        - 'manage_users': Can invite/remove group members
        """
        # System admins have all permissions
        if self.is_admin:
            return True
            
        # Users without groups have no permissions
        if not self.group:
            return False
        
        role_permissions = {
            self.Role.ADMIN: ['read', 'create', 'update', 'delete', 'manage_users'],
            self.Role.EDITOR: ['read', 'create', 'update'],
            self.Role.VIEWER: ['read'],
        }
        
        return permission in role_permissions.get(self.role, [])

class GroupInviteLink(TimeStampedModel):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Invite for {self.group.name} - {'Used' if self.is_used else 'Active'}"