from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .models import CustomUser, Group, GroupInviteLink
from .forms import CustomUserCreationForm
import uuid

def register_view(request, invite_token=None):
    """
    Handle user registration. If invite_token is provided, user joins that group.
    Otherwise, creates a new group for the user.
    """
    invite_link = None
    group_to_join = None
    
    if invite_token:
        try:
            invite_link = GroupInviteLink.objects.get(token=invite_token, is_used=False)
            group_to_join = invite_link.group
        except GroupInviteLink.DoesNotExist:
            messages.error(request, "Invalid or expired invite link.")
            return redirect('register')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            if group_to_join:
                # User is joining via invite
                user.group = group_to_join
                # Mark invite as used
                invite_link.is_used = True
                invite_link.save()
                messages.success(request, f"Welcome! You've joined the group '{group_to_join.name}'.")
            else:
                # Create new group for user
                group_name = f"{user.username}'s Group"
                new_group = Group.objects.create(name=group_name)
                user.group = new_group
                messages.success(request, f"Welcome! A new group '{group_name}' has been created for you.")
            
            user.save()
            
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'group_to_join': group_to_join,
        'invite_token': invite_token
    }
    return render(request, 'registration/register.html', context)

@login_required
def dashboard_view(request):
    """
    Main dashboard - shows user's group information and group-scoped data
    """
    user = request.user
    
    # Get users in the same group (for non-superusers)
    if user.is_superuser:
        # Superusers see all groups and users
        all_groups = Group.objects.all()
        all_users = CustomUser.objects.all()
        context = {
            'user': user,
            'all_groups': all_groups,
            'all_users': all_users,
            'is_superuser': True
        }
    else:
        # Regular users see only their group data
        group_users = CustomUser.objects.filter(group=user.group) if user.group else []
        context = {
            'user': user,
            'group': user.group,
            'group_users': group_users,
            'is_superuser': False
        }
    
    return render(request, 'wealthUser/dashboard.html', context)

@login_required
def create_invite_link(request):
    """
    Create an invite link for the user's group
    """
    if not request.user.group:
        messages.error(request, "You must be in a group to create invite links.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        invite_link = GroupInviteLink.objects.create(
            group=request.user.group,
            created_by=request.user
        )
        
        invite_url = request.build_absolute_uri(
            reverse('register_with_invite', args=[invite_link.token])
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            return JsonResponse({
                'success': True,
                'invite_url': invite_url,
                'token': str(invite_link.token)
            })
        else:
            messages.success(request, f"Invite link created: {invite_url}")
            return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def group_settings_view(request):
    """
    View for group-specific settings and management
    """
    if not request.user.group:
        messages.error(request, "You must be in a group to access group settings.")
        return redirect('dashboard')
    
    group = request.user.group
    group_members = CustomUser.objects.filter(group=group)
    active_invites = GroupInviteLink.objects.filter(group=group, is_used=False)
    
    context = {
        'group': group,
        'group_members': group_members,
        'active_invites': active_invites,
    }
    
    return render(request, 'wealthUser/group_settings.html', context)
