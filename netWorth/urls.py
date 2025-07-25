from django.urls import path
from . import views

app_name = 'networth'

urlpatterns = [
    # Summary endpoints
    path('api/v1/networth/summary/', views.NetWorthSummaryView.as_view(), name='summary'),
    
    # Asset endpoints
    path('api/v1/networth/assets/', views.AssetsView.as_view(), name='assets'),
    path('api/v1/networth/assets/<int:asset_id>/', views.AssetDetailView.as_view(), name='asset_detail'),
    
    # Liability endpoints
    path('api/v1/networth/liabilities/', views.LiabilitiesView.as_view(), name='liabilities'),
    path('api/v1/networth/liabilities/<int:liability_id>/', views.LiabilityDetailView.as_view(), name='liability_detail'),
]
