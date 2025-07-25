from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any
from .models import NetWorthItem


class AssetsValidator:
    """Validator class for asset-related operations"""
    
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.errors: List[str] = []
    
    def validate_required_fields(self) -> bool:
        """Validate that all required fields are present"""
        required_fields = ['name', 'value', 'asset_category']
        for field in required_fields:
            if field not in self.data:
                self.errors.append(f'Missing required field: {field}')
        return len(self.errors) == 0
    
    def validate_asset_category(self) -> bool:
        """Validate that the asset category is valid"""
        if 'asset_category' in self.data:
            valid_categories = [choice[0] for choice in NetWorthItem.ASSET_CATEGORIES]
            if self.data['asset_category'] not in valid_categories:
                self.errors.append('Invalid asset category')
                return False
        return True
    
    def validate_value_format(self) -> bool:
        """Validate that the value is in correct format and positive"""
        if 'value' in self.data:
            try:
                value = Decimal(str(self.data['value']))
                if value < 0:
                    self.errors.append('Value must be positive')
                    return False
                # Store the converted value for later use
                self.data['_validated_value'] = value
            except (InvalidOperation, ValueError):
                self.errors.append('Invalid value format')
                return False
        return True
    
    def validate(self) -> dict:
        """Run all validations and return success status with errors"""
        # Reset errors
        self.errors = []
        
        # Run all validation methods
        self.validate_required_fields()
        self.validate_asset_category()
        self.validate_value_format()
        
        # Return validation result
        is_valid = len(self.errors) == 0
        return {
            'is_valid': is_valid,
            'errors': self.errors,
            'data': self.data
        }


class LiabilitiesValidator:
    """Validator class for liability-related operations"""
    
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.errors: List[str] = []
    
    def validate_required_fields(self) -> bool:
        """Validate that all required fields are present"""
        required_fields = ['name', 'value']
        for field in required_fields:
            if field not in self.data:
                self.errors.append(f'Missing required field: {field}')
        return len(self.errors) == 0
    
    def validate_value_format(self) -> bool:
        """Validate that the value is in correct format and positive"""
        if 'value' in self.data:
            try:
                value = Decimal(str(self.data['value']))
                if value < 0:
                    self.errors.append('Value must be positive')
                    return False
                # Store the converted value for later use
                self.data['_validated_value'] = value
            except (InvalidOperation, ValueError):
                self.errors.append('Invalid value format')
                return False
        return True
    
    def validate(self) -> dict:
        """Run all validations and return success status with errors"""
        # Reset errors
        self.errors = []
        
        # Run all validation methods
        self.validate_required_fields()
        self.validate_value_format()
        
        # Return validation result
        is_valid = len(self.errors) == 0
        return {
            'is_valid': is_valid,
            'errors': self.errors,
            'data': self.data
        }


class AssetUpdateValidator:
    """Validator class for asset update operations"""
    
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.errors: List[str] = []
    
    def validate_value_format(self) -> bool:
        """Validate value format if provided"""
        if 'value' in self.data:
            try:
                value = Decimal(str(self.data['value']))
                if value < 0:
                    self.errors.append('Value must be positive')
                    return False
                # Store the converted value for later use
                self.data['_validated_value'] = value
            except (InvalidOperation, ValueError):
                self.errors.append('Invalid value format')
                return False
        return True
    
    def validate_asset_category(self) -> bool:
        """Validate asset category if provided"""
        if 'asset_category' in self.data:
            valid_categories = [choice[0] for choice in NetWorthItem.ASSET_CATEGORIES]
            if self.data['asset_category'] not in valid_categories:
                self.errors.append('Invalid asset category')
                return False
        return True
    
    def validate(self) -> dict:
        """Run all validations and return success status with errors"""
        # Reset errors
        self.errors = []
        
        # Run all validation methods
        self.validate_value_format()
        self.validate_asset_category()
        
        # Return validation result
        is_valid = len(self.errors) == 0
        return {
            'is_valid': is_valid,
            'errors': self.errors,
            'data': self.data
        }


class LiabilityUpdateValidator:
    """Validator class for liability update operations"""
    
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.errors: List[str] = []
    
    def validate_value_format(self) -> bool:
        """Validate value format if provided"""
        if 'value' in self.data:
            try:
                value = Decimal(str(self.data['value']))
                if value < 0:
                    self.errors.append('Value must be positive')
                    return False
                # Store the converted value for later use
                self.data['_validated_value'] = value
            except (InvalidOperation, ValueError):
                self.errors.append('Invalid value format')
                return False
        return True
    
    def validate(self) -> dict:
        """Run all validations and return success status with errors"""
        # Reset errors
        self.errors = []
        
        # Run all validation methods
        self.validate_value_format()
        
        # Return validation result
        is_valid = len(self.errors) == 0
        return {
            'is_valid': is_valid,
            'errors': self.errors,
            'data': self.data
        }
