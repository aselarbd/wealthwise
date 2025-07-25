from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any
from wealthUser.models import Group, TimeStampedModel


class NetWorthItem(TimeStampedModel):
    """Base model for Assets and Liabilities"""
    
    # Group scoping
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    ITEM_TYPES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
    ]
    
    ASSET_CATEGORIES = [
        ('SAVINGS', 'Savings'),
        ('INVESTMENTS', 'Investments'),
        ('PROPERTY', 'Property'),
        ('OTHER_ASSETS', 'Other Assets'),
    ]
    
    name = models.CharField(max_length=255)
    value = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    asset_category = models.CharField(
        max_length=20, 
        choices=ASSET_CATEGORIES, 
        null=True, 
        blank=True,
        help_text="Only applicable for Assets"
    )
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['item_type', 'name']
        indexes = [
            models.Index(fields=['group', 'item_type']),
            models.Index(fields=['group', 'asset_category']),
        ]
    
    def __str__(self) -> str:
        category_info = f" ({self.get_asset_category_display()})" if self.asset_category else ""
        return f"{self.name}{category_info} - ${self.value:,.2f}"
    
    def get_asset_category_display(self) -> str:
        """Get the human-readable display name for asset category"""
        if self.asset_category:
            # Convert choices tuple to dict for lookup
            choices_dict = dict(self.ASSET_CATEGORIES)
            return choices_dict.get(self.asset_category, self.asset_category)
        return ""
    
    def get_item_type_display(self) -> str:
        """Get the human-readable display name for item type"""
        choices_dict = dict(self.ITEM_TYPES)
        return choices_dict.get(self.item_type, self.item_type)
    
    def is_asset(self) -> bool:
        """Check if this item is an asset"""
        return self.item_type == 'ASSET'
    
    def is_liability(self) -> bool:
        """Check if this item is a liability"""
        return self.item_type == 'LIABILITY'
    
    def clean(self) -> None:
        """Validate that asset_category is only set for assets"""
        from django.core.exceptions import ValidationError
        
        if self.item_type == 'LIABILITY' and self.asset_category:
            raise ValidationError('Liabilities cannot have an asset category.')
        
        if self.item_type == 'ASSET' and not self.asset_category:
            raise ValidationError('Assets must have an asset category.')
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class NetWorthSummary:
    """Helper class to calculate net worth summaries for a group"""
    
    def __init__(self, group: Group) -> None:
        self.group = group
    
    def get_total_assets(self) -> Decimal:
        """Get total value of all assets"""
        return NetWorthItem.objects.filter(
            group=self.group, 
            item_type='ASSET'
        ).aggregate(
            total=models.Sum('value')
        )['total'] or Decimal('0.00')
    
    def get_total_liabilities(self) -> Decimal:
        """Get total value of all liabilities"""
        return NetWorthItem.objects.filter(
            group=self.group, 
            item_type='LIABILITY'
        ).aggregate(
            total=models.Sum('value')
        )['total'] or Decimal('0.00')
    
    def get_net_worth(self) -> Decimal:
        """Calculate net worth (assets - liabilities)"""
        return self.get_total_assets() - self.get_total_liabilities()
    
    def get_assets_by_category(self) -> List[Dict[str, Any]]:
        """Get assets grouped by category with totals"""
        from django.db.models import Sum
        
        return list(NetWorthItem.objects.filter(
            group=self.group, 
            item_type='ASSET'
        ).values('asset_category').annotate(
            total_value=Sum('value'),
            count=models.Count('id')
        ).order_by('asset_category'))
    
    def get_summary(self) -> Dict[str, Union[Decimal, List[Dict[str, Any]]]]:
        """Get complete net worth summary"""
        return {
            'total_assets': self.get_total_assets(),
            'total_liabilities': self.get_total_liabilities(),
            'net_worth': self.get_net_worth(),
            'assets_by_category': self.get_assets_by_category(),
        }
