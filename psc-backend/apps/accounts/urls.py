"""
URL configuration for accounts app.

API endpoints per BACKEND_STRUCTURE.md and IMPLEMENTATION_PLAN.md Step 2.1:
- POST /api/psc/auth/login/
- POST /api/psc/auth/refresh/
- POST /api/psc/auth/logout/
- GET /api/psc/auth/me/
"""

from django.urls import path

from .views import (
    LoginView,
    TokenRefreshView,
    LogoutView,
    CurrentUserView,
    CrewListView,
    CompanyLogoUploadView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('crew/', CrewListView.as_view(), name='crew-list'),
    path('company-logo/', CompanyLogoUploadView.as_view(), name='company-logo'),
]
