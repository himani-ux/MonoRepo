"""
Master data views - Read-only list endpoints.

Per BACKEND_STRUCTURE.md Section 10.10 - Master Data Endpoints
All endpoints are public (no auth required) as master data is reference data.
"""

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .models import (
    MOUMaster,
    PSCActionCode,
    PICMaster,
    PSCDefCategory,
    PSCDefSubcategory,
    PSCDefCode,
    CLCCategory,
    CLCItem,
)
from .serializers import (
    MOUSerializer,
    PSCActionCodeSerializer,
    PICSerializer,
    PSCDefCategorySerializer,
    PSCDefCodeSerializer,
    CLCCategorySerializer,
    CLCItemSerializer,
)


class MOUListView(generics.ListAPIView):
    """
    GET /api/psc/masters/mou/

    List all MOU regions.
    """
    permission_classes = [AllowAny]
    serializer_class = MOUSerializer

    def get_queryset(self):
        return MOUMaster.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'message': 'MOU list retrieved successfully'
        })


class PSCActionCodeListView(generics.ListAPIView):
    """
    GET /api/psc/masters/psc-action-codes/

    List all PSC action codes.
    """
    permission_classes = [AllowAny]
    serializer_class = PSCActionCodeSerializer

    def get_queryset(self):
        return PSCActionCode.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'message': 'PSC action codes retrieved successfully'
        })


class PICListView(generics.ListAPIView):
    """
    GET /api/psc/masters/pic/

    List all PIC (Person In Charge) codes.
    Query params:
    - department: Filter by department (Deck, Engine)
    """
    permission_classes = [AllowAny]
    serializer_class = PICSerializer

    def get_queryset(self):
        queryset = PICMaster.objects.all()

        # Filter by department if provided
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__iexact=department)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'message': 'PIC list retrieved successfully'
        })


class PSCDefCategoryListView(generics.ListAPIView):
    """
    GET /api/psc/masters/psc-def-categories/

    List all PSC deficiency categories.
    """
    permission_classes = [AllowAny]
    serializer_class = PSCDefCategorySerializer

    def get_queryset(self):
        return PSCDefCategory.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'message': 'PSC deficiency categories retrieved successfully'
        })


class PSCDefCodeListView(generics.ListAPIView):
    """
    GET /api/psc/masters/psc-def-codes/

    List PSC deficiency codes with search and filter.
    Query params:
    - search: Search in def_code or def_name
    - category: Filter by category_code (e.g., '07' for Fire safety)
    """
    permission_classes = [AllowAny]
    serializer_class = PSCDefCodeSerializer

    def get_queryset(self):
        queryset = PSCDefCode.objects.filter(is_active=True)

        # Search by code or name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(def_code__icontains=search) |
                Q(def_name__icontains=search)
            )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_code=category)

        return queryset

    def get_serializer_context(self):
        """Add category/subcategory lookup to context for serializer."""
        context = super().get_serializer_context()

        # Build category lookup dict
        categories = {
            cat.category_code: cat.category_name
            for cat in PSCDefCategory.objects.filter(is_active=True)
        }
        context['categories'] = categories

        # Build subcategory lookup dict
        subcategories = {
            sub.subcategory_code: sub.subcategory_name
            for sub in PSCDefSubcategory.objects.filter(is_active=True)
        }
        context['subcategories'] = subcategories

        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'count': queryset.count(),
            'message': 'PSC deficiency codes retrieved successfully'
        })


class CLCCategoryListView(generics.ListAPIView):
    """
    GET /api/psc/masters/clc-categories/

    List all CLC categories (for building hierarchy).
    """
    permission_classes = [AllowAny]
    serializer_class = CLCCategorySerializer

    def get_queryset(self):
        return CLCCategory.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'message': 'CLC categories retrieved successfully'
        })


class CLCListView(generics.ListAPIView):
    """
    GET /api/psc/masters/clc/

    List CLC items with search and filter.
    Query params:
    - search: Search in clc_code or item_name
    - type: Filter by category_type (Immediate_Action, Immediate_Condition, Root_Personal, Root_Job)
    - category_id: Filter by specific category_id
    """
    permission_classes = [AllowAny]
    serializer_class = CLCItemSerializer

    def get_queryset(self):
        queryset = CLCItem.objects.filter(is_active=True)

        # Search by code or name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(clc_code__icontains=search) |
                Q(item_name__icontains=search)
            )

        # Filter by category type
        category_type = self.request.query_params.get('type')
        if category_type:
            # Get category IDs that match this type
            category_ids = CLCCategory.objects.filter(
                category_type=category_type
            ).values_list('category_id', flat=True)
            queryset = queryset.filter(category_id__in=category_ids)

        # Filter by specific category
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_serializer_context(self):
        """Add category lookup to context for serializer."""
        context = super().get_serializer_context()

        # Build category lookup dict
        categories = {
            cat.category_id: {
                'code': cat.category_code,
                'name': cat.category_name,
                'type': cat.category_type,
            }
            for cat in CLCCategory.objects.all()
        }
        context['categories'] = categories

        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'count': queryset.count(),
            'message': 'CLC items retrieved successfully'
        })


class CLCHierarchyView(APIView):
    """
    GET /api/psc/masters/clc/hierarchy/

    Get CLC data in hierarchical format for tree/accordion display.
    Returns structure matching clc_library.json format.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Get all categories and items
        categories = CLCCategory.objects.all()
        items = CLCItem.objects.filter(is_active=True)

        # Build hierarchy
        hierarchy = {
            'immediate_causes': {
                'actions': {},
                'conditions': {},
            },
            'root_causes': {
                'personal_factors': {},
                'job_factors': {},
            },
        }

        # Group items by category
        items_by_category = {}
        for item in items:
            if item.category_id not in items_by_category:
                items_by_category[item.category_id] = []
            items_by_category[item.category_id].append({
                'code': item.clc_code,
                'name': item.item_name,
                'description': item.item_description,
            })

        # Build structure based on category type
        for cat in categories:
            if cat.category_type and cat.parent_id:
                cat_data = {
                    'name': cat.category_name,
                    'items': {
                        item['code']: item['name']
                        for item in items_by_category.get(cat.category_id, [])
                    }
                }

                if cat.category_type == 'Immediate_Action':
                    hierarchy['immediate_causes']['actions'][cat.category_code] = cat_data
                elif cat.category_type == 'Immediate_Condition':
                    hierarchy['immediate_causes']['conditions'][cat.category_code] = cat_data
                elif cat.category_type == 'Root_Personal':
                    hierarchy['root_causes']['personal_factors'][cat.category_code] = cat_data
                elif cat.category_type == 'Root_Job':
                    hierarchy['root_causes']['job_factors'][cat.category_code] = cat_data

        return Response({
            'data': hierarchy,
            'message': 'CLC hierarchy retrieved successfully'
        })
