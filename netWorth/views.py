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
from django.core.paginator import Paginator
from decimal import Decimal

from wealthWise.permissions import PermissionRequiredMixin
from wealthWise.middleware import GroupContext
from .models import NetWorthItem, NetWorthSummary
from .serializers import (
    AssetSerializer, 
    LiabilitySerializer,
    NetWorthSummarySerializer,
    AssetCategorySerializer
)


class NetWorthSummaryAPIView(PermissionRequiredMixin, APIView):
    """
    API endpoint for net worth summary with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    """
    required_permission = 'read'
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get net worth summary for user's group"""
        current_group = GroupContext.get_current_group()
        if not current_group:
            return Response(
                {'error': 'User must be assigned to a group'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        summary = NetWorthSummary(current_group)
        data = summary.get_summary()
        
        # Enhance assets_by_category with display names
        enhanced_categories = []
        for item in data['assets_by_category']:
            enhanced_categories.append({
                'asset_category': item['asset_category'],
                'asset_category_display': dict(NetWorthItem.ASSET_CATEGORIES).get(
                    item['asset_category'], item['asset_category']
                ),
                'total_value': item['total_value'],
                'count': item['count']
            })
        
        data['assets_by_category'] = enhanced_categories
        
        serializer = NetWorthSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssetsAPIView(PermissionRequiredMixin, APIView):
    """
    API endpoint for asset CRUD operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - POST: 'create' permission (admin, editor roles only)
    """
    permission_classes = [IsAuthenticated]

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'POST': 'create'
        }
        return [permissions.get(method, 'read')]

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

    def get(self, request):
        """List all assets for user's group with pagination"""
        current_group = GroupContext.get_current_group()
        if not current_group:
            return Response(
                {'error': 'User must be assigned to a group'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Get assets with automatic group filtering
        assets = NetWorthItem.objects.filter(item_type='ASSET').order_by('-created_at')
        
        # Implement pagination
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        
        paginator = Paginator(assets, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize the data
        serializer = AssetSerializer(page_obj.object_list, many=True)
        
        # Build paginated response
        response_data = {
            'count': paginator.count,
            'next': None,
            'previous': None,
            'assets': serializer.data
        }
        
        if page_obj.has_next():
            response_data['next'] = f"?page={page_obj.next_page_number()}&page_size={page_size}"
        
        if page_obj.has_previous():
            response_data['previous'] = f"?page={page_obj.previous_page_number()}&page_size={page_size}"
        
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new asset - requires 'create' permission"""
        current_group = GroupContext.get_current_group()
        if not current_group:
            return Response(
                {'error': 'User must be assigned to a group'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AssetSerializer(data=request.data)
        if serializer.is_valid():
            # Save with automatic group assignment
            serializer.save(group=current_group)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetDetailAPIView(PermissionRequiredMixin, APIView):
    """
    API endpoint for individual asset operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - PUT: 'update' permission (admin, editor roles only)
    - DELETE: 'delete' permission (admin role only)
    """
    permission_classes = [IsAuthenticated]

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return [permissions.get(method, 'read')]

    def check_permissions(self, request):
        """Check permissions based on HTTP method"""
        super().check_permissions(request)
        required_perms = self.get_permissions_for_method(request.method)
        for perm in required_perms:
            if not GroupContext.has_permission(perm):
                self.permission_denied(
                    request, 
                    message=f"Permission denied. Required permission: {perm}",
                    code=status.HTTP_403_FORBIDDEN
                )

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


class LiabilitiesAPIView(PermissionRequiredMixin, APIView):
    """
    API endpoint for liability CRUD operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - POST: 'create' permission (admin, editor roles only)
    """
    permission_classes = [IsAuthenticated]

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'POST': 'create'
        }
        return [permissions.get(method, 'read')]

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

    def get(self, request):
        """List all liabilities for user's group with pagination"""
        current_group = GroupContext.get_current_group()
        if not current_group:
            return Response(
                {'error': 'User must be assigned to a group'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Get liabilities with automatic group filtering
        liabilities = NetWorthItem.objects.filter(item_type='LIABILITY').order_by('-created_at')
        
        # Implement pagination
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        
        paginator = Paginator(liabilities, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize the data
        serializer = LiabilitySerializer(page_obj.object_list, many=True)
        
        # Build paginated response
        response_data = {
            'count': paginator.count,
            'next': None,
            'previous': None,
            'liabilities': serializer.data
        }
        
        if page_obj.has_next():
            response_data['next'] = f"?page={page_obj.next_page_number()}&page_size={page_size}"
        
        if page_obj.has_previous():
            response_data['previous'] = f"?page={page_obj.previous_page_number()}&page_size={page_size}"
        
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new liability - requires 'create' permission"""
        current_group = GroupContext.get_current_group()
        if not current_group:
            return Response(
                {'error': 'User must be assigned to a group'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = LiabilitySerializer(data=request.data)
        if serializer.is_valid():
            # Save with automatic group assignment
            serializer.save(group=current_group)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LiabilityDetailAPIView(PermissionRequiredMixin, APIView):
    """
    API endpoint for individual liability operations with role-based permissions.
    
    Permissions Required:
    - GET: 'read' permission (all roles: admin, editor, viewer)
    - PUT: 'update' permission (admin, editor roles only)
    - DELETE: 'delete' permission (admin role only)
    """
    permission_classes = [IsAuthenticated]

    def get_permissions_for_method(self, method):
        """Return required permission for each HTTP method"""
        permissions = {
            'GET': 'read',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return [permissions.get(method, 'read')]

    def check_permissions(self, request):
        """Check permissions based on HTTP method"""
        super().check_permissions(request)
        required_perms = self.get_permissions_for_method(request.method)
        for perm in required_perms:
            if not GroupContext.has_permission(perm):
                self.permission_denied(
                    request, 
                    message=f"Permission denied. Required permission: {perm}",
                    code=status.HTTP_403_FORBIDDEN
                )

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
