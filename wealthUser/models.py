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
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} ({self.group.name if self.group else 'No Group'})"

class GroupInviteLink(TimeStampedModel):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Invite for {self.group.name} - {'Used' if self.is_used else 'Active'}"