from django.urls import path
from . import views

app_name = 'networth'

urlpatterns = [
    # Summary endpoints
    path(app_name + '/summary/', views.NetWorthSummaryAPIView.as_view(), name='summary'),
    
    # Asset endpoints
    path(app_name + '/assets/', views.AssetsAPIView.as_view(), name='assets'),
    path(app_name + '/assets/<int:asset_id>/', views.AssetDetailAPIView.as_view(), name='asset_detail'),
    
    # Liability endpoints
    path(app_name + '/liabilities/', views.LiabilitiesAPIView.as_view(), name='liabilities'),
    path(app_name + '/liabilities/<int:liability_id>/', views.LiabilityDetailAPIView.as_view(), name='liability_detail'),
]
