from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(http_method_names=['get', 'post']), name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/<uuid:invite_token>/', views.register_view, name='register_with_invite'),
    
    # Dashboard and main views
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Group management
    path('group/settings/', views.group_settings_view, name='group_settings'),
    path('group/create-invite/', views.create_invite_link, name='create_invite_link'),
]
