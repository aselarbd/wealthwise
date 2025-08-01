from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
import json

from wealthUser.models import Group
from wealthWise.middleware import GroupContext
from .models import NetWorthItem
from .services import NetWorthService

User = get_user_model()


class BaseTestCaseWithGroupContext(TestCase):
    """Base test class that properly sets up group context for permission testing"""
    
    def setUp(self):
        """Set up shared test data and group context"""
        super().setUp()
        self.client = Client()
        self.group = Group.objects.create(name="Test Group")
        
        # Create standard test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            group=self.group,
            role=User.Role.ADMIN
        )
        
        # Create standard test assets and liabilities
        self.asset = NetWorthItem.objects.create(
            group=self.group,
            name="Test Asset",
            value=Decimal("10000.00"),
            item_type="ASSET",
            asset_category="SAVINGS"
        )
        
        self.liability = NetWorthItem.objects.create(
            group=self.group,
            name="Test Liability",
            value=Decimal("5000.00"),
            item_type="LIABILITY"
        )
        
    def login_and_set_context(self, username, password, user=None, group=None):
        """Helper to login and set group context like middleware would"""
        login_success = self.client.login(username=username, password=password)
        if login_success and user and group:
            GroupContext.set_current_user(user)
            GroupContext.set_current_group(group)
        return login_success
    
    def login_as_test_user(self):
        """Convenience method to login as the standard test user"""
        return self.login_and_set_context("testuser", "testpass123", self.user, self.group)
    
    def _test_crud_operations(self, user, username, password, can_create=True, can_update=True, can_delete=True):
        """Helper method to test CRUD operations for different user roles"""
        self.login_and_set_context(username, password, user, self.group)
        
        # Test READ operations (always allowed)
        response = self.client.get('/api/v1/networth/summary/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/api/v1/networth/assets/')
        self.assertEqual(response.status_code, 200)
        
        # Test CREATE operations
        asset_data = {
            'name': f'Asset by {username}',
            'value': '2000.00',
            'asset_category': 'INVESTMENTS',
            'description': f'Created by {username}'
        }
        response = self.client.post(
            '/api/v1/networth/assets/',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        expected_status = 201 if can_create else 403
        self.assertEqual(response.status_code, expected_status)
        
        # Test UPDATE operations
        update_data = {'name': f'Updated by {username}', 'value': '15000.00', 'asset_category': 'INVESTMENTS'}
        response = self.client.put(
            f'/api/v1/networth/assets/{self.asset.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        expected_status = 200 if can_update else 403
        self.assertEqual(response.status_code, expected_status)
        
        # Test DELETE operations
        response = self.client.delete(f'/api/v1/networth/assets/{self.asset.id}/')
        expected_status = 204 if can_delete else 403
        self.assertEqual(response.status_code, expected_status)


class NetWorthModelTests(TestCase):
    """Test cases for NetWorth models"""
    
    def setUp(self):
        """Set up test data"""
        self.group = Group.objects.create(name="Test Group")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            group=self.group,
            role=User.Role.ADMIN  # Admin role for full test access
        )
    
    def test_create_asset(self):
        """Test creating an asset"""
        asset = NetWorthItem.objects.create(
            group=self.group,
            name="Test Asset",
            value=Decimal("1000.00"),
            item_type="ASSET",
            asset_category="SAVINGS",
            description="Test asset description"
        )
        
        self.assertEqual(asset.name, "Test Asset")
        self.assertEqual(asset.value, Decimal("1000.00"))
        self.assertEqual(asset.item_type, "ASSET")
        self.assertEqual(asset.asset_category, "SAVINGS")
        self.assertEqual(asset.group, self.group)
        self.assertTrue(asset.created_at)
        self.assertTrue(asset.updated_at)
    
    def test_create_liability(self):
        """Test creating a liability"""
        liability = NetWorthItem.objects.create(
            group=self.group,
            name="Test Liability",
            value=Decimal("5000.00"),
            item_type="LIABILITY",
            description="Test liability description"
        )
        
        self.assertEqual(liability.name, "Test Liability")
        self.assertEqual(liability.value, Decimal("5000.00"))
        self.assertEqual(liability.item_type, "LIABILITY")
        self.assertIsNone(liability.asset_category)
        self.assertEqual(liability.group, self.group)
    
    def test_asset_category_display(self):
        """Test asset category display method"""
        asset = NetWorthItem.objects.create(
            group=self.group,
            name="Test Asset",
            value=Decimal("1000.00"),
            item_type="ASSET",
            asset_category="PROPERTY"
        )
        
        self.assertEqual(asset.get_asset_category_display(), "Property")
    
    def test_str_representation(self):
        """Test string representation of NetWorthItem"""
        asset = NetWorthItem.objects.create(
            group=self.group,
            name="Test Asset",
            value=Decimal("1000.00"),
            item_type="ASSET",
            asset_category="SAVINGS"
        )
        
        # Test the string representation format
        self.assertIn("Test Asset", str(asset))
        self.assertIn("Asset", str(asset))
        self.assertIn("1,000.00", str(asset))


class NetWorthSummaryTests(TestCase):
    """Test cases for NetWorthService class"""
    
    def setUp(self):
        """Set up test data"""
        self.group = Group.objects.create(name="Test Group")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            group=self.group,
            role=User.Role.ADMIN  # Admin role for full test access
        )
        
        # Create test assets
        NetWorthItem.objects.create(
            group=self.group,
            name="Savings Asset",
            value=Decimal("10000.00"),
            item_type="ASSET",
            asset_category="SAVINGS"
        )
        NetWorthItem.objects.create(
            group=self.group,
            name="Investment Asset",
            value=Decimal("25000.00"),
            item_type="ASSET",
            asset_category="INVESTMENTS"
        )
        NetWorthItem.objects.create(
            group=self.group,
            name="Property Asset",
            value=Decimal("300000.00"),
            item_type="ASSET",
            asset_category="PROPERTY"
        )
        
        # Create test liabilities
        NetWorthItem.objects.create(
            group=self.group,
            name="Mortgage",
            value=Decimal("200000.00"),
            item_type="LIABILITY"
        )
        NetWorthItem.objects.create(
            group=self.group,
            name="Credit Card",
            value=Decimal("5000.00"),
            item_type="LIABILITY"
        )
    
    def test_get_total_assets(self):
        """Test total assets calculation"""
        summary = NetWorthService(self.group)
        total_assets = summary.get_total_assets()
        expected_total = Decimal("335000.00")  # 10000 + 25000 + 300000
        self.assertEqual(total_assets, expected_total)
    
    def test_get_total_liabilities(self):
        """Test total liabilities calculation"""
        summary = NetWorthService(self.group)
        total_liabilities = summary.get_total_liabilities()
        expected_total = Decimal("205000.00")  # 200000 + 5000
        self.assertEqual(total_liabilities, expected_total)
    
    def test_get_net_worth(self):
        """Test net worth calculation"""
        summary = NetWorthService(self.group)
        net_worth = summary.get_net_worth()
        expected_net_worth = Decimal("130000.00")  # 335000 - 205000
        self.assertEqual(net_worth, expected_net_worth)
    
    def test_get_assets_by_category(self):
        """Test assets by category breakdown"""
        summary = NetWorthService(self.group)
        assets_by_category = summary.get_assets_by_category()
        
        # Should have 3 categories
        self.assertEqual(len(assets_by_category), 3)
        
        # Check each category
        savings_category = next(cat for cat in assets_by_category if cat['asset_category'] == 'SAVINGS')
        self.assertEqual(savings_category['total_value'], Decimal("10000.00"))
        self.assertEqual(savings_category['count'], 1)
        
        investments_category = next(cat for cat in assets_by_category if cat['asset_category'] == 'INVESTMENTS')
        self.assertEqual(investments_category['total_value'], Decimal("25000.00"))
        self.assertEqual(investments_category['count'], 1)
        
        property_category = next(cat for cat in assets_by_category if cat['asset_category'] == 'PROPERTY')
        self.assertEqual(property_category['total_value'], Decimal("300000.00"))
        self.assertEqual(property_category['count'], 1)
    
    def test_get_summary(self):
        """Test complete summary data"""
        summary = NetWorthService(self.group)
        summary_data = summary.get_summary()
        
        self.assertEqual(summary_data['total_assets'], Decimal("335000.00"))
        self.assertEqual(summary_data['total_liabilities'], Decimal("205000.00"))
        self.assertEqual(summary_data['net_worth'], Decimal("130000.00"))
        self.assertEqual(len(summary_data['assets_by_category']), 3)
    
    def test_empty_group_summary(self):
        """Test summary for group with no assets/liabilities"""
        empty_group = Group.objects.create(name="Empty Group")
        summary = NetWorthService(empty_group)
        
        self.assertEqual(summary.get_total_assets(), Decimal("0.00"))
        self.assertEqual(summary.get_total_liabilities(), Decimal("0.00"))
        self.assertEqual(summary.get_net_worth(), Decimal("0.00"))
        
    def test_financial_ratios(self):
        """Test financial ratios calculation"""
        summary = NetWorthService(self.group)
        ratios = summary.get_financial_ratios()
        
        # Expected: 205000 / 335000 * 100 = ~61.19%
        expected_ratio = Decimal("61.19")
        self.assertEqual(ratios['debt_to_asset_ratio'], expected_ratio)
        self.assertEqual(ratios['financial_health_status'], "Fair")
        self.assertEqual(ratios['net_worth'], Decimal("130000.00"))
        
    def test_financial_ratios_no_assets(self):
        """Test financial ratios with no assets"""
        empty_group = Group.objects.create(name="Empty Group")
        summary = NetWorthService(empty_group)
        ratios = summary.get_financial_ratios()
        
        self.assertEqual(ratios['debt_to_asset_ratio'], Decimal("0.00"))
        self.assertEqual(ratios['financial_health_status'], "No Assets")
        self.assertEqual(ratios['net_worth'], Decimal("0.00"))
        self.assertEqual(len(summary.get_assets_by_category()), 0)


class NetWorthViewTests(BaseTestCaseWithGroupContext):
    """Test cases for NetWorth views"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()  # This now handles all the setup
    
    def test_summary_view_authenticated(self):
        """Test summary view with authenticated user"""
        self.login_as_test_user()
        
        response = self.client.get('/api/v1/networth/summary/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(f"{float(data['total_assets']):.2f}", '10000.00')
        self.assertEqual(f"{float(data['total_liabilities']):.2f}", '5000.00')
        self.assertEqual(f"{float(data['net_worth']):.2f}", '5000.00')
    
    def test_summary_view_unauthenticated(self):
        """Test summary view without authentication"""
        response = self.client.get('/api/v1/networth/summary/')
        # DRF returns 403 Forbidden instead of 302 redirect for API endpoints
        self.assertEqual(response.status_code, 403)
    
    def test_assets_list_view(self):
        """Test assets list view"""
        self.login_as_test_user()
        
        response = self.client.get('/api/v1/networth/assets/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['assets']), 1)
        self.assertEqual(data['assets'][0]['name'], 'Test Asset')
        self.assertEqual(f"{float(data['assets'][0]['value']):.2f}", '10000.00')
    
    def test_create_asset(self):
        """Test creating a new asset"""
        self.login_as_test_user()
        
        asset_data = {
            'name': 'New Asset',
            'value': '2000.00',
            'asset_category': 'INVESTMENTS',
            'description': 'New test asset'
        }
        
        response = self.client.post(
            '/api/v1/networth/assets/',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'New Asset')
        self.assertEqual(f"{float(data['value']):.2f}", '2000.00')
        self.assertEqual(data['asset_category'], 'INVESTMENTS')
        
        # Verify asset was created in database
        self.assertTrue(NetWorthItem.objects.filter(name='New Asset').exists())
    
    def test_create_asset_invalid_data(self):
        """Test creating asset with invalid data"""
        self.client.login(username="testuser", password="testpass123")
        
        invalid_data = {
            'name': 'Invalid Asset',
            'value': 'not_a_number',
            'asset_category': 'INVALID_CATEGORY'
        }
        
        response = self.client.post(
            '/api/v1/networth/assets/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        # DRF serializers return errors in different format than custom validators
        self.assertTrue('value' in data or 'asset_category' in data or 'errors' in data)
    
    def test_update_asset(self):
        """Test updating an existing asset"""
        self.login_as_test_user()
        
        update_data = {
            'name': 'Updated Asset',
            'value': '15000.00',
            'asset_category': 'SAVINGS',
        }
        
        response = self.client.put(
            f'/api/v1/networth/assets/{self.asset.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Updated Asset')
        self.assertEqual(f"{float(data['value']):.2f}", '15000.00')
        
        # Verify asset was updated in database
        updated_asset = NetWorthItem.objects.get(id=self.asset.id)
        self.assertEqual(updated_asset.name, 'Updated Asset')
        self.assertEqual(updated_asset.value, Decimal('15000.00'))
    
    def test_delete_asset(self):
        """Test deleting an asset"""
        self.login_as_test_user()
        
        response = self.client.delete(f'/api/v1/networth/assets/{self.asset.id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify asset was deleted from database
        self.assertFalse(NetWorthItem.objects.filter(id=self.asset.id).exists())
    
    def test_liabilities_list_view(self):
        """Test liabilities list view"""
        self.login_as_test_user()
        
        response = self.client.get('/api/v1/networth/liabilities/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['liabilities']), 1)
        self.assertEqual(data['liabilities'][0]['name'], 'Test Liability')
        self.assertEqual(f"{float(data['liabilities'][0]['value']):.2f}", '5000.00')
    
    def test_create_liability(self):
        """Test creating a new liability"""
        self.login_as_test_user()
        
        liability_data = {
            'name': 'New Liability',
            'value': '3000.00',
            'description': 'New test liability'
        }
        
        response = self.client.post(
            '/api/v1/networth/liabilities/',
            data=json.dumps(liability_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'New Liability')
        self.assertEqual(f"{float(data['value']):.2f}", '3000.00')
        
        # Verify liability was created in database
        self.assertTrue(NetWorthItem.objects.filter(name='New Liability').exists())
    
    def test_update_liability(self):
        """Test updating an existing liability"""
        self.login_as_test_user()
        
        update_data = {
            'name': 'Updated Liability',
            'value': '7000.00'
        }
        
        response = self.client.put(
            f'/api/v1/networth/liabilities/{self.liability.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Updated Liability')
        self.assertEqual(f"{float(data['value']):.2f}", '7000.00')
        
        # Verify liability was updated in database
        updated_liability = NetWorthItem.objects.get(id=self.liability.id)
        self.assertEqual(updated_liability.name, 'Updated Liability')
        self.assertEqual(updated_liability.value, Decimal('7000.00'))
    
    def test_delete_liability(self):
        """Test deleting a liability"""
        self.login_as_test_user()
        
        response = self.client.delete(f'/api/v1/networth/liabilities/{self.liability.id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify liability was deleted from database
        self.assertFalse(NetWorthItem.objects.filter(id=self.liability.id).exists())
    
    def test_user_without_group_access_denied(self):
        """Test that users without a group cannot access endpoints"""
        user_without_group = User.objects.create_user(
            username="nogroupuser",
            email="nogroup@example.com",
            password="testpass123",
            role=User.Role.ADMIN  # Even admin role won't help without group
        )
        
        self.login_and_set_context("nogroupuser", "testpass123", user_without_group, None)
        
        response = self.client.get('/api/v1/networth/summary/')
        # Changed expectation from 400 to 403 - permission denied is more accurate for DRF
        self.assertEqual(response.status_code, 403)
        
        data = response.json()
        # The error message might be different due to DRF permission system
        self.assertIn('error', data)
    
    def test_group_isolation(self):
        """Test that users can only see their own group's data"""
        # Create another group and user
        other_group = Group.objects.create(name="Other Group")
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123",
            group=other_group,
            role=User.Role.ADMIN  # Admin role for full test access
        )
        
        # Create asset for other group
        NetWorthItem.objects.create(
            group=other_group,
            name="Other Group Asset",
            value=Decimal("50000.00"),
            item_type="ASSET",
            asset_category="SAVINGS"
        )
        
        # Login as original user and check they can't see other group's data
        self.login_as_test_user()
        
        response = self.client.get('/api/v1/networth/assets/')
        data = response.json()
        
        # Should only see their own group's asset
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['assets'][0]['name'], 'Test Asset')
        
        # Check that summary doesn't include other group's data
        response = self.client.get('/api/v1/networth/summary/')
        data = response.json()
        self.assertEqual(f"{float(data['total_assets']):.2f}", '10000.00')  # Not 60000.00


class RoleBasedPermissionTests(BaseTestCaseWithGroupContext):
    """
    Test cases for Step 2: Enhanced Permissions
    
    Tests role-based access control for different user types:
    - Admin: Full CRUD access + user management
    - Editor: Read, Create, Update (no delete)
    - Viewer: Read-only access
    """
    
    def setUp(self):
        """Set up test data with different user roles"""
        super().setUp()  # Gets the base group and test user (admin)
        
        # Create additional users with different roles  
        self.admin_user = self.user  # Use the admin user from base class
        
        self.editor_user = User.objects.create_user(
            username="editor",
            email="editor@example.com",
            password="testpass123",
            group=self.group,
            role=User.Role.EDITOR
        )
        
        self.viewer_user = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="testpass123",
            group=self.group,
            role=User.Role.VIEWER
        )
        # Note: self.asset and self.liability are already created by base class
    
    def test_admin_permissions(self):
        """Test that admin users have full CRUD access"""
        self._test_crud_operations(
            user=self.admin_user, 
            username="testuser", 
            password="testpass123",
            can_create=True, 
            can_update=True, 
            can_delete=True
        )
    
    def test_editor_permissions(self):
        """Test that editor users can read, create, and update but not delete"""
        self._test_crud_operations(
            user=self.editor_user,
            username="editor",
            password="testpass123", 
            can_create=True,
            can_update=True,
            can_delete=False
        )
    
    def test_viewer_permissions(self):
        """Test that viewer users can only read data"""
        self._test_crud_operations(
            user=self.viewer_user,
            username="viewer", 
            password="testpass123",
            can_create=False,
            can_update=False,
            can_delete=False
        )
    
    def test_liability_permissions_consistency(self):
        """Test that liability operations follow the same permission rules as assets"""
        
        # Test Admin - full access to liabilities
        self.login_and_set_context("testuser", "testpass123", self.admin_user, self.group)
        
        liability_data = {
            'name': 'Admin Liability',
            'value': '8000.00',
            'description': 'Created by admin'
        }
        response = self.client.post(
            '/api/v1/networth/liabilities/',
            data=json.dumps(liability_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        response = self.client.delete(f'/api/v1/networth/liabilities/{self.liability.id}/')
        self.assertEqual(response.status_code, 204)
        
        # Test Viewer - read-only access to liabilities
        self.login_and_set_context("viewer", "testpass123", self.viewer_user, self.group)
        
        response = self.client.get('/api/v1/networth/liabilities/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            '/api/v1/networth/liabilities/',
            data=json.dumps(liability_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_system_admin_override(self):
        """Test that system admins (is_admin=True) bypass group role restrictions"""
        # Create system admin
        system_admin = User.objects.create_user(
            username="systemadmin",
            email="systemadmin@example.com",
            password="testpass123",
            group=self.group,
            role=User.Role.VIEWER,  # Even as viewer role
            is_admin=True  # System admin override
        )
        
        self.login_and_set_context("systemadmin", "testpass123", system_admin, self.group)
        
        # System admin can delete even with viewer role
        response = self.client.delete(f'/api/v1/networth/assets/{self.asset.id}/')
        self.assertEqual(response.status_code, 204)
    
    def test_user_permission_method(self):
        """Test the has_group_permission method on User model"""
        # Admin has all permissions
        self.assertTrue(self.admin_user.has_group_permission('read'))
        self.assertTrue(self.admin_user.has_group_permission('create'))
        self.assertTrue(self.admin_user.has_group_permission('update'))
        self.assertTrue(self.admin_user.has_group_permission('delete'))
        self.assertTrue(self.admin_user.has_group_permission('manage_users'))
        
        # Editor has limited permissions
        self.assertTrue(self.editor_user.has_group_permission('read'))
        self.assertTrue(self.editor_user.has_group_permission('create'))
        self.assertTrue(self.editor_user.has_group_permission('update'))
        self.assertFalse(self.editor_user.has_group_permission('delete'))
        self.assertFalse(self.editor_user.has_group_permission('manage_users'))
        
        # Viewer has minimal permissions
        self.assertTrue(self.viewer_user.has_group_permission('read'))
        self.assertFalse(self.viewer_user.has_group_permission('create'))
        self.assertFalse(self.viewer_user.has_group_permission('update'))
        self.assertFalse(self.viewer_user.has_group_permission('delete'))
        self.assertFalse(self.viewer_user.has_group_permission('manage_users'))
    
    def test_role_display_values(self):
        """Test that role display values are correct"""
        self.assertEqual(self.admin_user.get_role_display(), 'Administrator')
        self.assertEqual(self.editor_user.get_role_display(), 'Editor')
        self.assertEqual(self.viewer_user.get_role_display(), 'Viewer')
