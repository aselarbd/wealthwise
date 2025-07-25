from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
import json

from wealthUser.models import Group
from .models import NetWorthItem, NetWorthSummary
from .validators import (
    AssetsValidator, 
    LiabilitiesValidator, 
    AssetUpdateValidator, 
    LiabilityUpdateValidator
)

User = get_user_model()


class NetWorthModelTests(TestCase):
    """Test cases for NetWorth models"""
    
    def setUp(self):
        """Set up test data"""
        self.group = Group.objects.create(name="Test Group")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            group=self.group
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
    """Test cases for NetWorthSummary helper class"""
    
    def setUp(self):
        """Set up test data"""
        self.group = Group.objects.create(name="Test Group")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            group=self.group
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
        summary = NetWorthSummary(self.group)
        total_assets = summary.get_total_assets()
        expected_total = Decimal("335000.00")  # 10000 + 25000 + 300000
        self.assertEqual(total_assets, expected_total)
    
    def test_get_total_liabilities(self):
        """Test total liabilities calculation"""
        summary = NetWorthSummary(self.group)
        total_liabilities = summary.get_total_liabilities()
        expected_total = Decimal("205000.00")  # 200000 + 5000
        self.assertEqual(total_liabilities, expected_total)
    
    def test_get_net_worth(self):
        """Test net worth calculation"""
        summary = NetWorthSummary(self.group)
        net_worth = summary.get_net_worth()
        expected_net_worth = Decimal("130000.00")  # 335000 - 205000
        self.assertEqual(net_worth, expected_net_worth)
    
    def test_get_assets_by_category(self):
        """Test assets by category breakdown"""
        summary = NetWorthSummary(self.group)
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
        summary = NetWorthSummary(self.group)
        summary_data = summary.get_summary()
        
        self.assertEqual(summary_data['total_assets'], Decimal("335000.00"))
        self.assertEqual(summary_data['total_liabilities'], Decimal("205000.00"))
        self.assertEqual(summary_data['net_worth'], Decimal("130000.00"))
        self.assertEqual(len(summary_data['assets_by_category']), 3)
    
    def test_empty_group_summary(self):
        """Test summary for group with no assets/liabilities"""
        empty_group = Group.objects.create(name="Empty Group")
        summary = NetWorthSummary(empty_group)
        
        self.assertEqual(summary.get_total_assets(), Decimal("0.00"))
        self.assertEqual(summary.get_total_liabilities(), Decimal("0.00"))
        self.assertEqual(summary.get_net_worth(), Decimal("0.00"))
        self.assertEqual(len(summary.get_assets_by_category()), 0)


class ValidatorTests(TestCase):
    """Test cases for validator classes"""
    
    def test_assets_validator_valid_data(self):
        """Test AssetsValidator with valid data"""
        valid_data = {
            'name': 'Test Asset',
            'value': '1000.00',
            'asset_category': 'SAVINGS',
            'description': 'Test description'
        }
        
        validator = AssetsValidator(valid_data)
        result = validator.validate()
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['data']['_validated_value'], Decimal('1000.00'))
    
    def test_assets_validator_missing_required_fields(self):
        """Test AssetsValidator with missing required fields"""
        invalid_data = {
            'description': 'Missing required fields'
        }
        
        validator = AssetsValidator(invalid_data)
        result = validator.validate()
        
        self.assertFalse(result['is_valid'])
        self.assertEqual(len(result['errors']), 3)  # name, value, asset_category
        self.assertIn('Missing required field: name', result['errors'])
        self.assertIn('Missing required field: value', result['errors'])
        self.assertIn('Missing required field: asset_category', result['errors'])
    
    def test_assets_validator_invalid_category(self):
        """Test AssetsValidator with invalid asset category"""
        invalid_data = {
            'name': 'Test Asset',
            'value': '1000.00',
            'asset_category': 'INVALID_CATEGORY'
        }
        
        validator = AssetsValidator(invalid_data)
        result = validator.validate()
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid asset category', result['errors'])
    
    def test_assets_validator_invalid_value_format(self):
        """Test AssetsValidator with invalid value format"""
        invalid_data = {
            'name': 'Test Asset',
            'value': 'not_a_number',
            'asset_category': 'SAVINGS'
        }
        
        validator = AssetsValidator(invalid_data)
        result = validator.validate()
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid value format', result['errors'])
    
    def test_assets_validator_negative_value(self):
        """Test AssetsValidator with negative value"""
        invalid_data = {
            'name': 'Test Asset',
            'value': '-1000.00',
            'asset_category': 'SAVINGS'
        }
        
        validator = AssetsValidator(invalid_data)
        result = validator.validate()
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Value must be positive', result['errors'])
    
    def test_liabilities_validator_valid_data(self):
        """Test LiabilitiesValidator with valid data"""
        valid_data = {
            'name': 'Test Liability',
            'value': '5000.00',
            'description': 'Test description'
        }
        
        validator = LiabilitiesValidator(valid_data)
        result = validator.validate()
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['data']['_validated_value'], Decimal('5000.00'))
    
    def test_liabilities_validator_missing_required_fields(self):
        """Test LiabilitiesValidator with missing required fields"""
        invalid_data = {
            'description': 'Missing required fields'
        }
        
        validator = LiabilitiesValidator(invalid_data)
        result = validator.validate()
        
        self.assertFalse(result['is_valid'])
        self.assertEqual(len(result['errors']), 2)  # name, value
        self.assertIn('Missing required field: name', result['errors'])
        self.assertIn('Missing required field: value', result['errors'])
    
    def test_asset_update_validator_partial_update(self):
        """Test AssetUpdateValidator with partial data"""
        update_data = {
            'value': '1500.00'
        }
        
        validator = AssetUpdateValidator(update_data)
        result = validator.validate()
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['data']['_validated_value'], Decimal('1500.00'))
    
    def test_asset_update_validator_invalid_category(self):
        """Test AssetUpdateValidator with invalid category"""
        update_data = {
            'asset_category': 'INVALID_CATEGORY'
        }
        
        validator = AssetUpdateValidator(update_data)
        result = validator.validate()
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid asset category', result['errors'])
    
    def test_liability_update_validator_valid_data(self):
        """Test LiabilityUpdateValidator with valid data"""
        update_data = {
            'name': 'Updated Liability',
            'value': '3000.00'
        }
        
        validator = LiabilityUpdateValidator(update_data)
        result = validator.validate()
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['data']['_validated_value'], Decimal('3000.00'))


class NetWorthViewTests(TestCase):
    """Test cases for NetWorth views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.group = Group.objects.create(name="Test Group")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            group=self.group
        )
        
        # Create test asset and liability
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
    
    def test_summary_view_authenticated(self):
        """Test summary view with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get('/api/v1/networth/summary/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(f"{float(data['total_assets']):.2f}", '10000.00')
        self.assertEqual(f"{float(data['total_liabilities']):.2f}", '5000.00')
        self.assertEqual(f"{float(data['net_worth']):.2f}", '5000.00')
    
    def test_summary_view_unauthenticated(self):
        """Test summary view without authentication"""
        response = self.client.get('/api/v1/networth/summary/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_assets_list_view(self):
        """Test assets list view"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get('/api/v1/networth/assets/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['assets']), 1)
        self.assertEqual(data['assets'][0]['name'], 'Test Asset')
        self.assertEqual(f"{float(data['assets'][0]['value']):.2f}", '10000.00')
    
    def test_create_asset(self):
        """Test creating a new asset"""
        self.client.login(username="testuser", password="testpass123")
        
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
        self.assertIn('errors', data)
    
    def test_update_asset(self):
        """Test updating an existing asset"""
        self.client.login(username="testuser", password="testpass123")
        
        update_data = {
            'name': 'Updated Asset',
            'value': '15000.00'
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
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.delete(f'/api/v1/networth/assets/{self.asset.id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify asset was deleted from database
        self.assertFalse(NetWorthItem.objects.filter(id=self.asset.id).exists())
    
    def test_liabilities_list_view(self):
        """Test liabilities list view"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get('/api/v1/networth/liabilities/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['liabilities']), 1)
        self.assertEqual(data['liabilities'][0]['name'], 'Test Liability')
        self.assertEqual(f"{float(data['liabilities'][0]['value']):.2f}", '5000.00')
    
    def test_create_liability(self):
        """Test creating a new liability"""
        self.client.login(username="testuser", password="testpass123")
        
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
        self.client.login(username="testuser", password="testpass123")
        
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
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.delete(f'/api/v1/networth/liabilities/{self.liability.id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify liability was deleted from database
        self.assertFalse(NetWorthItem.objects.filter(id=self.liability.id).exists())
    
    def test_user_without_group_access_denied(self):
        """Test that users without a group cannot access endpoints"""
        user_without_group = User.objects.create_user(
            username="nogroupuser",
            email="nogroup@example.com",
            password="testpass123"
        )
        
        self.client.login(username="nogroupuser", password="testpass123")
        
        response = self.client.get('/api/v1/networth/summary/')
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('User must be assigned to a group', data['error'])
    
    def test_group_isolation(self):
        """Test that users can only see their own group's data"""
        # Create another group and user
        other_group = Group.objects.create(name="Other Group")
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123",
            group=other_group
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
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.get('/api/v1/networth/assets/')
        data = response.json()
        
        # Should only see their own group's asset
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['assets'][0]['name'], 'Test Asset')
        
        # Check that summary doesn't include other group's data
        response = self.client.get('/api/v1/networth/summary/')
        data = response.json()
        self.assertEqual(f"{float(data['total_assets']):.2f}", '10000.00')  # Not 60000.00
