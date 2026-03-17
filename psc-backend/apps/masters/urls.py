"""
Master data URL routes.

Per BACKEND_STRUCTURE.md Section 10.10 - Master Data Endpoints
"""

from django.urls import path

from .views import (
    MOUListView,
    PSCActionCodeListView,
    PICListView,
    PSCDefCategoryListView,
    PSCDefCodeListView,
    CLCCategoryListView,
    CLCListView,
    CLCHierarchyView,
)

app_name = 'masters'

urlpatterns = [
    # MOU
    path('mou/', MOUListView.as_view(), name='mou-list'),

    # PSC Action Codes
    path('psc-action-codes/', PSCActionCodeListView.as_view(), name='psc-action-codes-list'),

    # PIC (Person In Charge)
    path('pic/', PICListView.as_view(), name='pic-list'),

    # PSC Deficiency Codes
    path('psc-def-categories/', PSCDefCategoryListView.as_view(), name='psc-def-categories-list'),
    path('psc-def-codes/', PSCDefCodeListView.as_view(), name='psc-def-codes-list'),

    # CLC (Comprehensive List of Causes)
    path('clc-categories/', CLCCategoryListView.as_view(), name='clc-categories-list'),
    path('clc/', CLCListView.as_view(), name='clc-list'),
    path('clc/hierarchy/', CLCHierarchyView.as_view(), name='clc-hierarchy'),
]
