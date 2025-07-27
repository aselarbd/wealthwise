"""
Django REST Framework Views for NetWorth App

These views provide REST API endpoints for managing assets, liabilities,
and net worth calculations with proper HTTP status codes, serialization,
and permission controls.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from wealthWise.permissions import PermissionRequiredMixin
from wealthWise.middleware import GroupContext
from .models import NetWorthItem
from .services import NetWorthService
from .serializers import (
    AssetSerializer, 
    LiabilitySerializer,
    NetWorthSummarySerializer,
    AssetCategorySerializer
)


class BaseNetWorthView(PermissionRequiredMixin, APIView):
    """
    Base view class for NetWorth API endpoints.
    Provides common functionality for group validation and service initialization.
    """
    permission_classes = [IsAuthenticated]
    
    def get_current_group(self):
        """Get current group with validation"""
        current_group = GroupContext.get_current_group()
        if not current_group:
            return None
        return current_group
    
    def validate_group_access(self):
        """Validate group access and return appropriate response if invalid"""
        current_group = self.get_current_group()
        if not current_group:
            return Response(
                {'error': 'User must be assigned to a group'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return None
    
    def get_service(self):
        """Get NetWorthService instance for current group"""
        current_group = self.get_current_group()
        return NetWorthService(current_group)


class BaseDynamicPermissionView(BaseNetWorthView):
    """
    Base view class for NetWorth endpoints with dynamic permission checking.
    Handles permission checking based on HTTP method.
    """
    
    def get_permissions_for_method(self, method):
        """
        Return required permission for each HTTP method.
        Override this method in subclasses to define method-specific permissions.
        """
        raise NotImplementedError("Subclasses must implement get_permissions_for_method")
    
    def check_permissions(self, request):
        """Check permissions based on HTTP method"""
        super().check_permissions(request)
        required_perms = self.get_permissions_for_method(request.method)
        for perm in required_perms:
            if not GroupContext.has_permission(perm):
                self.permission_denied(
                    request, 
                    message=f"Permission denied. Required permission: {perm}"
                )


class NetWorthSummaryAPIView(BaseNetWorthView):
    """
    API endpoint for net worth summary with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    """
    required_permission = 'read'

    def get(self, request):
        """Get net worth summary for user's group"""
        # Validate group access
        group_error = self.validate_group_access()
        if group_error:
            return group_error

        # Get data from service
        service = self.get_service()
        data = service.get_enhanced_summary()
        
        serializer = NetWorthSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssetsAPIView(BaseDynamicPermissionView):
    """
    API endpoint for asset CRUD operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - POST: 'create' permission (admin, editor roles only)
    """

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'POST': 'create'
        }
        return [permissions.get(method, 'read')]

    def get(self, request):
        """List all assets for user's group with pagination"""
        # Validate group access
        group_error = self.validate_group_access()
        if group_error:
            return group_error

        # Extract pagination parameters
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        
        # Get paginated data from service
        service = self.get_service()
        paginated_data = service.get_paginated_assets(page, page_size)
        
        # Serialize the results
        serializer = AssetSerializer(paginated_data['results'], many=True)
        
        # Build response with pagination URLs
        response_data = {
            'count': paginated_data['count'],
            'next': None,
            'previous': None,
            'assets': serializer.data
        }
        
        if paginated_data['next']:
            response_data['next'] = f"?page={paginated_data['next']}&page_size={page_size}"
        
        if paginated_data['previous']:
            response_data['previous'] = f"?page={paginated_data['previous']}&page_size={page_size}"
        
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new asset - requires 'create' permission"""
        # Validate group access
        group_error = self.validate_group_access()
        if group_error:
            return group_error

        # Get current group for saving
        current_group = self.get_current_group()
        
        serializer = AssetSerializer(data=request.data)
        if serializer.is_valid():
            # Save with automatic group assignment
            serializer.save(group=current_group)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetDetailAPIView(BaseDynamicPermissionView):
    """
    API endpoint for individual asset operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - PUT: 'update' permission (admin, editor roles only)
    - DELETE: 'delete' permission (admin role only)
    """

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return [permissions.get(method, 'read')]

    def get_object(self, asset_id):
        """Helper method to get asset with automatic group filtering"""
        return get_object_or_404(
            NetWorthItem,
            id=asset_id,
            item_type='ASSET'
        )

    def get(self, request, asset_id):
        """Get a specific asset"""
        asset = self.get_object(asset_id)
        serializer = AssetSerializer(asset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, asset_id):
        """Update an asset - requires 'update' permission"""
        asset = self.get_object(asset_id)
        serializer = AssetSerializer(asset, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, asset_id):
        """Partially update an asset - requires 'update' permission"""
        return self.put(request, asset_id)

    def delete(self, request, asset_id):
        """Delete an asset - requires 'delete' permission"""
        asset = self.get_object(asset_id)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LiabilitiesAPIView(BaseDynamicPermissionView):
    """
    API endpoint for liability CRUD operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - POST: 'create' permission (admin, editor roles only)
    """

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'POST': 'create'
        }
        return [permissions.get(method, 'read')]

    def get(self, request):
        """List all liabilities for user's group with pagination"""
        # Validate group access
        group_error = self.validate_group_access()
        if group_error:
            return group_error

        # Extract pagination parameters
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        
        # Get paginated data from service
        service = self.get_service()
        paginated_data = service.get_paginated_liabilities(page, page_size)
        
        # Serialize the results
        serializer = LiabilitySerializer(paginated_data['results'], many=True)
        
        # Build response with pagination URLs
        response_data = {
            'count': paginated_data['count'],
            'next': None,
            'previous': None,
            'liabilities': serializer.data
        }
        
        if paginated_data['next']:
            response_data['next'] = f"?page={paginated_data['next']}&page_size={page_size}"
        
        if paginated_data['previous']:
            response_data['previous'] = f"?page={paginated_data['previous']}&page_size={page_size}"
        
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new liability - requires 'create' permission"""
        # Validate group access
        group_error = self.validate_group_access()
        if group_error:
            return group_error

        # Get current group for saving
        current_group = self.get_current_group()
        
        serializer = LiabilitySerializer(data=request.data)
        if serializer.is_valid():
            # Save with automatic group assignment
            serializer.save(group=current_group)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LiabilityDetailAPIView(BaseDynamicPermissionView):
    """
    API endpoint for individual liability operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - PUT: 'update' permission (admin, editor roles only)
    - DELETE: 'delete' permission (admin role only)
    """

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return [permissions.get(method, 'read')]

    def get_object(self, liability_id):
        """Helper method to get liability with automatic group filtering"""
        return get_object_or_404(
            NetWorthItem,
            id=liability_id,
            item_type='LIABILITY'
        )

    def get(self, request, liability_id):
        """Get a specific liability"""
        liability = self.get_object(liability_id)
        serializer = LiabilitySerializer(liability)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, liability_id):
        """Update a liability - requires 'update' permission"""
        liability = self.get_object(liability_id)
        serializer = LiabilitySerializer(liability, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, liability_id):
        """Partially update a liability - requires 'update' permission"""
        return self.put(request, liability_id)

    def delete(self, request, liability_id):
        """Delete a liability - requires 'delete' permission"""
        liability = self.get_object(liability_id)
        liability.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
