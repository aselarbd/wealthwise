from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Union
from .models import NetWorthItem, NetWorthSummary
from .validators import (
    AssetsValidator, 
    LiabilitiesValidator, 
    AssetUpdateValidator, 
    LiabilityUpdateValidator
)


@method_decorator(login_required, name='dispatch')
class NetWorthSummaryView(View):
    """API endpoint for net worth summary"""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        summary = NetWorthSummary(request.user.group)
        data = summary.get_summary()
        
        # Convert Decimal to string for JSON serialization
        return JsonResponse({
            'total_assets': str(data['total_assets']),
            'total_liabilities': str(data['total_liabilities']),
            'net_worth': str(data['net_worth']),
            'assets_by_category': [
                {
                    'category': item['asset_category'],
                    'category_display': dict(NetWorthItem.ASSET_CATEGORIES).get(item['asset_category'], ''),
                    'total_value': str(item['total_value']),
                    'count': item['count']
                }
                for item in data['assets_by_category']
            ]
        })


@method_decorator(login_required, name='dispatch')
class AssetsView(View):
    """API endpoint for asset CRUD operations"""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """List all assets for user's group"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        assets = NetWorthItem.objects.filter(
            group=request.user.group,
            item_type='ASSET'
        )
        
        data: List[Dict[str, Any]] = [
            {
                'id': asset.id,
                'name': asset.name,
                'value': str(asset.value),
                'asset_category': asset.asset_category,
                'asset_category_display': asset.get_asset_category_display(),
                'description': asset.description,
                'created_at': asset.created_at.isoformat(),
                'updated_at': asset.updated_at.isoformat(),
            }
            for asset in assets
        ]
        
        summary = NetWorthSummary(request.user.group)
        
        return JsonResponse({
            'assets': data,
            'total_assets': str(summary.get_total_assets()),
            'count': len(data)
        })
    
    def post(self, request: HttpRequest) -> JsonResponse:
        """Create a new asset"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Use validator for all other validations
        validator = AssetsValidator(data)
        validation_result = validator.validate()
        
        if not validation_result['is_valid']:
            return JsonResponse({'errors': validation_result['errors']}, status=400)
        
        # Get the validated data (including the converted value)
        validated_data = validation_result['data']
        
        # Create asset
        asset = NetWorthItem.objects.create(
            group=request.user.group,
            name=validated_data['name'],
            value=validated_data['_validated_value'],  # Use the validated Decimal value
            item_type='ASSET',
            asset_category=validated_data['asset_category'],
            description=validated_data.get('description', '')
        )
        
        return JsonResponse({
            'id': asset.id,
            'name': asset.name,
            'value': str(asset.value),
            'asset_category': asset.asset_category,
            'asset_category_display': asset.get_asset_category_display(),
            'description': asset.description,
            'created_at': asset.created_at.isoformat(),
        }, status=201)


@method_decorator(login_required, name='dispatch')
class AssetDetailView(View):
    """API endpoint for individual asset operations"""
    
    def get_asset(self, request: HttpRequest, asset_id: int) -> NetWorthItem:
        """Helper method to get asset with group scope"""
        return get_object_or_404(
            NetWorthItem,
            id=asset_id,
            group=request.user.group,
            item_type='ASSET'
        )
    
    def put(self, request: HttpRequest, asset_id: int) -> JsonResponse:
        """Update an asset"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        asset = self.get_asset(request, asset_id)
        
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Use validator for all validations
        validator = AssetUpdateValidator(data)
        validation_result = validator.validate()
        
        if not validation_result['is_valid']:
            return JsonResponse({'errors': validation_result['errors']}, status=400)
        
        # Get the validated data
        validated_data = validation_result['data']
        
        # Update fields if provided
        if 'name' in validated_data:
            asset.name = validated_data['name']
        
        if 'value' in validated_data:
            asset.value = validated_data['_validated_value']  # Use validated Decimal value
        
        if 'asset_category' in validated_data:
            asset.asset_category = validated_data['asset_category']
        
        if 'description' in validated_data:
            asset.description = validated_data['description']
        
        asset.save()
        
        return JsonResponse({
            'id': asset.id,
            'name': asset.name,
            'value': str(asset.value),
            'asset_category': asset.asset_category,
            'asset_category_display': asset.get_asset_category_display(),
            'description': asset.description,
            'updated_at': asset.updated_at.isoformat(),
        })
    
    def delete(self, request: HttpRequest, asset_id: int) -> JsonResponse:
        """Delete an asset"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        asset = self.get_asset(request, asset_id)
        asset.delete()
        
        return JsonResponse({'message': 'Asset deleted successfully'}, status=204)


@method_decorator(login_required, name='dispatch')
class LiabilitiesView(View):
    """API endpoint for liability CRUD operations"""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """List all liabilities for user's group"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        liabilities = NetWorthItem.objects.filter(
            group=request.user.group,
            item_type='LIABILITY'
        )
        
        data: List[Dict[str, Any]] = [
            {
                'id': liability.id,
                'name': liability.name,
                'value': str(liability.value),
                'description': liability.description,
                'created_at': liability.created_at.isoformat(),
                'updated_at': liability.updated_at.isoformat(),
            }
            for liability in liabilities
        ]
        
        summary = NetWorthSummary(request.user.group)
        
        return JsonResponse({
            'liabilities': data,
            'total_liabilities': str(summary.get_total_liabilities()),
            'count': len(data)
        })
    
    def post(self, request: HttpRequest) -> JsonResponse:
        """Create a new liability"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Use validator for all validations
        validator = LiabilitiesValidator(data)
        validation_result = validator.validate()
        
        if not validation_result['is_valid']:
            return JsonResponse({'errors': validation_result['errors']}, status=400)
        
        # Get the validated data
        validated_data = validation_result['data']
        
        # Create liability
        liability = NetWorthItem.objects.create(
            group=request.user.group,
            name=validated_data['name'],
            value=validated_data['_validated_value'],  # Use validated Decimal value
            item_type='LIABILITY',
            description=validated_data.get('description', '')
        )
        
        return JsonResponse({
            'id': liability.id,
            'name': liability.name,
            'value': str(liability.value),
            'description': liability.description,
            'created_at': liability.created_at.isoformat(),
        }, status=201)


@method_decorator(login_required, name='dispatch')
class LiabilityDetailView(View):
    """API endpoint for individual liability operations"""
    
    def get_liability(self, request: HttpRequest, liability_id: int) -> NetWorthItem:
        """Helper method to get liability with group scope"""
        return get_object_or_404(
            NetWorthItem,
            id=liability_id,
            group=request.user.group,
            item_type='LIABILITY'
        )
    
    def put(self, request: HttpRequest, liability_id: int) -> JsonResponse:
        """Update a liability"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        liability = self.get_liability(request, liability_id)
        
        try:
            data: Dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Use validator for all validations
        validator = LiabilityUpdateValidator(data)
        validation_result = validator.validate()
        
        if not validation_result['is_valid']:
            return JsonResponse({'errors': validation_result['errors']}, status=400)
        
        # Get the validated data
        validated_data = validation_result['data']
        
        # Update fields if provided
        if 'name' in validated_data:
            liability.name = validated_data['name']
        
        if 'value' in validated_data:
            liability.value = validated_data['_validated_value']  # Use validated Decimal value
        
        if 'description' in validated_data:
            liability.description = validated_data['description']
        
        liability.save()
        
        return JsonResponse({
            'id': liability.id,
            'name': liability.name,
            'value': str(liability.value),
            'description': liability.description,
            'updated_at': liability.updated_at.isoformat(),
        })
    
    def delete(self, request: HttpRequest, liability_id: int) -> JsonResponse:
        """Delete a liability"""
        if not request.user.group:
            return JsonResponse({'error': 'User must be assigned to a group'}, status=400)
        
        liability = self.get_liability(request, liability_id)
        liability.delete()
        
        return JsonResponse({'message': 'Liability deleted successfully'}, status=204)
