from django.db import models
from decimal import Decimal
from typing import Dict, List, Any, Union
from .models import NetWorthItem
from wealthUser.models import Group


class NetWorthService:
    """Service class for net worth calculations and business logic"""
    
    def __init__(self, group: Group) -> None:
        self.group = group
    
    def get_total_assets(self) -> Decimal:
        """Get total value of all assets for the group"""
        return NetWorthItem.objects.filter(
            group=self.group, 
            item_type='ASSET'
        ).aggregate(
            total=models.Sum('value')
        )['total'] or Decimal('0.00')
    
    def get_total_liabilities(self) -> Decimal:
        """Get total value of all liabilities for the group"""
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
        """Get assets grouped by category with totals and counts"""
        from django.db.models import Sum, Count
        
        return list(NetWorthItem.objects.filter(
            group=self.group, 
            item_type='ASSET'
        ).values('asset_category').annotate(
            total_value=Sum('value'),
            count=Count('id')
        ).order_by('asset_category'))
    
    def get_liabilities_summary(self) -> List[Dict[str, Any]]:
        """Get liabilities summary with individual items"""
        return list(NetWorthItem.objects.filter(
            group=self.group,
            item_type='LIABILITY'
        ).values('name', 'value', 'description').order_by('name'))
    
    def get_summary(self) -> Dict[str, Union[Decimal, List[Dict[str, Any]]]]:
        """Get complete net worth summary with all financial data"""
        return {
            'total_assets': self.get_total_assets(),
            'total_liabilities': self.get_total_liabilities(),
            'net_worth': self.get_net_worth(),
            'assets_by_category': self.get_assets_by_category(),
            'liabilities_summary': self.get_liabilities_summary(),
        }
    
    def get_enhanced_summary(self) -> dict:
        """Get net worth summary with enhanced display names for UI"""
        summary = self.get_summary()
        
        # Enhance assets_by_category with display names
        enhanced_categories = []
        for item in summary['assets_by_category']:
            enhanced_categories.append({
                'asset_category': item['asset_category'],
                'asset_category_display': dict(NetWorthItem.ASSET_CATEGORIES).get(
                    item['asset_category'], item['asset_category']
                ),
                'total_value': item['total_value'],
                'count': item['count']
            })
        
        summary['assets_by_category'] = enhanced_categories
        return summary
    
    def get_paginated_assets(self, page: int = 1, page_size: int = 20) -> dict:
        """Get paginated assets for the group"""
        from django.core.paginator import Paginator
        
        assets = NetWorthItem.objects.filter(
            group=self.group, 
            item_type='ASSET'
        ).order_by('-created_at')
        
        paginator = Paginator(assets, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'results': list(page_obj.object_list),
            'page_size': page_size,
            'current_page': page
        }
    
    def get_paginated_liabilities(self, page: int = 1, page_size: int = 20) -> dict:
        """Get paginated liabilities for the group"""
        from django.core.paginator import Paginator
        
        liabilities = NetWorthItem.objects.filter(
            group=self.group, 
            item_type='LIABILITY'
        ).order_by('-created_at')
        
        paginator = Paginator(liabilities, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'results': list(page_obj.object_list),
            'page_size': page_size,
            'current_page': page
        }
    
    def get_financial_ratios(self) -> dict:
        """Calculate financial health ratios"""
        total_assets = self.get_total_assets()
        total_liabilities = self.get_total_liabilities()
        
        if total_assets == Decimal('0.00'):
            debt_to_asset_ratio = Decimal('0.00')
            financial_health = "No Assets"
        else:
            debt_to_asset_ratio = (total_liabilities / total_assets) * 100
            
            if debt_to_asset_ratio <= 30:
                financial_health = "Excellent"
            elif debt_to_asset_ratio <= 50:
                financial_health = "Good"
            elif debt_to_asset_ratio <= 70:
                financial_health = "Fair"
            else:
                financial_health = "Needs Attention"
        
        return {
            'debt_to_asset_ratio': debt_to_asset_ratio.quantize(Decimal('0.01')),
            'financial_health_status': financial_health,
            'net_worth': self.get_net_worth(),
        }
