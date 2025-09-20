"""
Django REST Framework Serializers for NetWorth App

These serializers handle data validation, transformation, and serialization
for the NetWorth API endpoints, replacing the custom validator classes
with DRF's standardized approach.
"""

from rest_framework import serializers
from .models import NetWorthItem


class NetWorthItemSerializer(serializers.ModelSerializer):
    """
    Serializer for NetWorthItem model.
    Handles both Assets and Liabilities with appropriate validation.
    """
    
    class Meta:
        model = NetWorthItem
        fields = [
            'id', 'name', 'value', 'item_type', 'asset_category', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_value(self, value):
        """Ensure value is positive"""
        if value <= 0:
            raise serializers.ValidationError("Value must be positive.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        item_type = data.get('item_type')
        asset_category = data.get('asset_category')
        
        # Asset-specific validation
        if item_type == 'ASSET':
            if not asset_category:
                raise serializers.ValidationError({
                    'asset_category': 'Asset category is required for assets.'
                })
            
            # Validate asset category choices
            valid_categories = [choice[0] for choice in NetWorthItem.ASSET_CATEGORIES]
            if asset_category not in valid_categories:
                raise serializers.ValidationError({
                    'asset_category': f'Invalid asset category. Must be one of: {valid_categories}'
                })
        
        # Liability-specific validation  
        elif item_type == 'LIABILITY':
            if asset_category:
                raise serializers.ValidationError({
                    'asset_category': 'Liabilities cannot have an asset category.'
                })
        
        return data


class AssetSerializer(NetWorthItemSerializer):
    """
    Specialized serializer for Assets.
    Automatically sets item_type to ASSET and requires asset_category.
    """
    
    class Meta(NetWorthItemSerializer.Meta):
        fields = [
            'id', 'name', 'value', 'asset_category', 
            'description', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Automatically set item_type for assets
        data['item_type'] = 'ASSET'
        return super().validate(data)


class LiabilitySerializer(NetWorthItemSerializer):
    """
    Specialized serializer for Liabilities.
    Automatically sets item_type to LIABILITY and excludes asset_category.
    """
    
    class Meta(NetWorthItemSerializer.Meta):
        fields = [
            'id', 'name', 'value', 'description', 
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Automatically set item_type for liabilities
        data['item_type'] = 'LIABILITY'
        data['asset_category'] = None
        return super().validate(data)


class AssetCategorySerializer(serializers.Serializer):
    """
    Serializer for asset category summary data.
    """
    asset_category = serializers.CharField()
    asset_category_display = serializers.CharField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    count = serializers.IntegerField()


class NetWorthSummarySerializer(serializers.Serializer):
    """
    Serializer for NetWorth summary response.
    Provides a standardized format for summary data.
    """
    total_assets = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_liabilities = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_worth = serializers.DecimalField(max_digits=15, decimal_places=2)
    assets_by_category = AssetCategorySerializer(many=True)


class AssetListSerializer(serializers.Serializer):
    """
    Serializer for paginated asset list response.
    """
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True, required=False)
    previous = serializers.URLField(allow_null=True, required=False)
    assets = AssetSerializer(many=True)


class LiabilityListSerializer(serializers.Serializer):
    """
    Serializer for paginated liability list response.
    """
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True, required=False)
    previous = serializers.URLField(allow_null=True, required=False)
    liabilities = LiabilitySerializer(many=True)
