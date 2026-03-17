"""DefIntel reports URL configuration."""

from django.urls import path

from .defintel_checklist import VesselPrepExportView, VesselPrepPreviewView
from .defintel_prediction import DefIntelPredictDefCodesView
from .defintel_views import OpenSourceImportView

app_name = 'reports'

urlpatterns = [
    path('opensource/import/', OpenSourceImportView.as_view(), name='opensource-import'),
    path('vessel-prep/preview/', VesselPrepPreviewView.as_view(), name='vessel-prep-preview'),
    path('vessel-prep/export/', VesselPrepExportView.as_view(), name='vessel-prep-export'),
    path('defintel/predict-defcodes/', DefIntelPredictDefCodesView.as_view(), name='defintel-predict-defcodes'),
]
