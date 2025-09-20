from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from .models import Group, GroupInviteLink, CustomUser
import uuid


User = get_user_model()


class GroupModelTest(TestCase):
    """Test cases for the Group model"""
    
    def setUp(self):
        self.group = Group.objects.create(name="Test Group")
    
    def test_group_creation(self):
        """Test that a group can be created successfully"""
        self.assertEqual(self.group.name, "Test Group")
        self.assertIsNotNone(self.group.created_at)
        self.assertIsNotNone(self.group.updated_at)
    
    def test_group_str_method(self):
        """Test the string representation of a group"""
        self.assertEqual(str(self.group), "Test Group")


class CustomUserModelTest(TestCase):
    """Test cases for the CustomUser model"""
    
    def setUp(self):
        self.group = Group.objects.create(name="Test Group")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            group=self.group
        )
    
    def test_user_creation(self):
        """Test that a custom user can be created successfully"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.group, self.group)
        self.assertFalse(self.user.is_admin)
        self.assertTrue(self.user.check_password("testpass123"))
    
    def test_user_str_method_with_group(self):
        """Test the string representation of a user with a group"""
        expected_str = f"testuser ({self.group.name})"
        self.assertEqual(str(self.user), expected_str)
    
    def test_user_str_method_without_group(self):
        """Test the string representation of a user without a group"""
        user_no_group = CustomUser.objects.create_user(
            username="nogroupuser",
            password="testpass123"
        )
        expected_str = "nogroupuser (No Group)"
        self.assertEqual(str(user_no_group), expected_str)
    
    def test_user_admin_flag(self):
        """Test the is_admin flag functionality"""
        admin_user = CustomUser.objects.create_user(
            username="adminuser",
            password="testpass123",
            group=self.group,
            is_admin=True
        )
        self.assertTrue(admin_user.is_admin)
    
    def test_user_group_cascade_on_delete(self):
        """Test that user's group can be set to NULL when group is deleted"""
        group_id = self.group.id
        self.group.delete()
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertIsNone(self.user.group)


class GroupInviteLinkModelTest(TestCase):
    """Test cases for the GroupInviteLink model"""
    
    def setUp(self):
        self.group = Group.objects.create(name="Test Group")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            group=self.group
        )
        self.invite_link = GroupInviteLink.objects.create(
            group=self.group,
            created_by=self.user
        )
    
    def test_invite_link_creation(self):
        """Test that an invite link can be created successfully"""
        self.assertEqual(self.invite_link.group, self.group)
        self.assertEqual(self.invite_link.created_by, self.user)
        self.assertFalse(self.invite_link.is_used)
        self.assertIsInstance(self.invite_link.token, uuid.UUID)
        self.assertIsNotNone(self.invite_link.created_at)
    
    def test_invite_link_str_method_active(self):
        """Test the string representation of an active invite link"""
        expected_str = f"Invite for {self.group.name} - Active"
        self.assertEqual(str(self.invite_link), expected_str)
    
    def test_invite_link_str_method_used(self):
        """Test the string representation of a used invite link"""
        self.invite_link.is_used = True
        self.invite_link.save()
        expected_str = f"Invite for {self.group.name} - Used"
        self.assertEqual(str(self.invite_link), expected_str)
    
    def test_invite_link_token_uniqueness(self):
        """Test that invite link tokens are unique"""
        # Create another invite link
        invite_link2 = GroupInviteLink.objects.create(
            group=self.group,
            created_by=self.user
        )
        self.assertNotEqual(self.invite_link.token, invite_link2.token)
    
    def test_invite_link_cascade_delete_with_group(self):
        """Test that invite links are deleted when group is deleted"""
        invite_id = self.invite_link.id
        self.group.delete()
        
        with self.assertRaises(GroupInviteLink.DoesNotExist):
            GroupInviteLink.objects.get(id=invite_id)
    
    def test_invite_link_cascade_delete_with_user(self):
        """Test that invite links are deleted when creator is deleted"""
        invite_id = self.invite_link.id
        self.user.delete()
        
        with self.assertRaises(GroupInviteLink.DoesNotExist):
            GroupInviteLink.objects.get(id=invite_id)


class UserViewsTest(TestCase):
    """Test cases for user-related views"""
    
    def setUp(self):
        self.client = Client()
        self.group = Group.objects.create(name="Test Group")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            group=self.group
        )
        self.superuser = CustomUser.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@test.com"
        )
    
    def test_register_view_get(self):
        """Test that register view loads correctly"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register")
        self.assertContains(response, "Username:")
    
    def test_register_view_post_creates_new_group(self):
        """Test that registering without invite creates new group"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        
        # Should redirect to dashboard after successful registration
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        
        # Check that user was created
        new_user = CustomUser.objects.get(username='newuser')
        self.assertIsNotNone(new_user.group)
        self.assertEqual(new_user.group.name, "newuser's Group")
    
    def test_register_with_invite_token(self):
        """Test registering with a valid invite token"""
        # Create an invite link
        invite_link = GroupInviteLink.objects.create(
            group=self.group,
            created_by=self.user
        )
        
        response = self.client.post(
            reverse('register_with_invite', args=[invite_link.token]), 
            {
                'username': 'inviteduser',
                'password1': 'complexpass123',
                'password2': 'complexpass123'
            }
        )
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        
        # Check that user joined the existing group
        invited_user = CustomUser.objects.get(username='inviteduser')
        self.assertEqual(invited_user.group, self.group)
        
        # Check that invite link is marked as used
        invite_link.refresh_from_db()
        self.assertTrue(invite_link.is_used)
    
    def test_register_with_invalid_invite_token(self):
        """Test registering with an invalid invite token"""
        invalid_token = uuid.uuid4()
        response = self.client.get(
            reverse('register_with_invite', args=[invalid_token])
        )
        
        # Should redirect to regular register with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('register'))
    
    def test_register_with_used_invite_token(self):
        """Test registering with an already used invite token"""
        # Create and mark invite link as used
        invite_link = GroupInviteLink.objects.create(
            group=self.group,
            created_by=self.user,
            is_used=True
        )
        
        response = self.client.get(
            reverse('register_with_invite', args=[invite_link.token])
        )
        
        # Should redirect to regular register with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('register'))
    
    def test_login_view(self):
        """Test the login view"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")
    
    def test_login_functionality(self):
        """Test actual login functionality"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_dashboard_view_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/dashboard/')
    
    def test_dashboard_view_regular_user(self):
        """Test dashboard view for regular user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Test Group')
        self.assertNotContains(response, 'All Groups (Superuser View)')
    
    def test_dashboard_view_superuser(self):
        """Test dashboard view for superuser"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin')
        self.assertContains(response, 'All Groups (Superuser View)')
    
    def test_create_invite_link_requires_login(self):
        """Test that creating invite link requires authentication"""
        response = self.client.post(reverse('create_invite_link'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/group/create-invite/')
    
    def test_create_invite_link_requires_group(self):
        """Test that creating invite link requires user to be in a group"""
        # Create user without group
        no_group_user = CustomUser.objects.create_user(
            username='nogroupuser',
            password='testpass123'
        )
        
        self.client.login(username='nogroupuser', password='testpass123')
        response = self.client.post(reverse('create_invite_link'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_create_invite_link_success(self):
        """Test successful invite link creation"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('create_invite_link'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        
        # Check that invite link was created
        invite_links = GroupInviteLink.objects.filter(
            group=self.group, 
            created_by=self.user,
            is_used=False
        )
        self.assertEqual(invite_links.count(), 1)
    
    def test_group_settings_view_requires_login(self):
        """Test that group settings requires authentication"""
        response = self.client.get(reverse('group_settings'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/group/settings/')
    
    def test_group_settings_view_requires_group(self):
        """Test that group settings requires user to be in a group"""
        # Create user without group
        no_group_user = CustomUser.objects.create_user(
            username='nogroupuser',
            password='testpass123'
        )
        
        self.client.login(username='nogroupuser', password='testpass123')
        response = self.client.get(reverse('group_settings'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_group_settings_view_success(self):
        """Test successful group settings view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('group_settings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Group Settings: Test Group')
        self.assertContains(response, 'testuser')


class AdminIntegrationTest(TestCase):
    """Test cases for admin integration"""
    
    def setUp(self):
        self.superuser = CustomUser.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@test.com'
        )
        self.group = Group.objects.create(name="Test Group")
        self.regular_user = CustomUser.objects.create_user(
            username='regularuser',
            password='testpass123',
            group=self.group
        )
    
    def test_admin_can_access_all_models(self):
        """Test that admin interface is properly configured"""
        from django.contrib import admin
        from .models import Group, CustomUser, GroupInviteLink
        
        # Check that models are registered
        self.assertIn(Group, admin.site._registry)
        self.assertIn(CustomUser, admin.site._registry)
        self.assertIn(GroupInviteLink, admin.site._registry)
