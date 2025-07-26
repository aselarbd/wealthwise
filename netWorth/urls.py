from django.urls import path
from . import views

app_name = 'networth'

urlpatterns = [
    # Summary endpoints
    path('api/v1/networth/summary/', views.NetWorthSummaryAPIView.as_view(), name='summary'),
    
    # Asset endpoints
    path('api/v1/networth/assets/', views.AssetsAPIView.as_view(), name='assets'),
    path('api/v1/networth/assets/<int:asset_id>/', views.AssetDetailAPIView.as_view(), name='asset_detail'),
    
    # Liability endpoints
    path('api/v1/networth/liabilities/', views.LiabilitiesAPIView.as_view(), name='liabilities'),
    path('api/v1/networth/liabilities/<int:liability_id>/', views.LiabilityDetailAPIView.as_view(), name='liability_detail'),
]
