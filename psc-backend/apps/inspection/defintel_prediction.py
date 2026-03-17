"""
Phase 4 DefIntel prediction endpoint (probability with Bayesian smoothing).
"""

import calendar
from collections import defaultdict
from datetime import date

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .deficiency_models import Deficiency
from .defintel_access import can_access_defintel_reports
from .defintel_checklist import _apply_user_access_scope
from .defintel_models import OpenSourceDeficiencyRecord
from .defintel_views import _normalize_def_code, _normalize_text

CONTEXT_PORT = 'PORT'
CONTEXT_MOU = 'MOU'
WINDOW_ALL_TIME = 'ALL_TIME'
WINDOW_LAST_24_MONTHS = 'LAST_24_MONTHS'

DEFAULT_ALPHA = 100
DEFAULT_TOP_N = 20


def _shift_months_back(anchor: date, months: int) -> date:
    year = anchor.year
    month = anchor.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class DefIntelPredictionQuerySerializer(serializers.Serializer):
    context = serializers.ChoiceField(choices=[CONTEXT_PORT, CONTEXT_MOU])
    port = serializers.CharField(required=False, allow_blank=False)
    mou = serializers.CharField(required=False, allow_blank=False)
    window = serializers.ChoiceField(
        choices=[WINDOW_ALL_TIME, WINDOW_LAST_24_MONTHS],
        required=False,
        default=WINDOW_LAST_24_MONTHS,
    )
    top_n = serializers.IntegerField(required=False, min_value=1, max_value=100, default=DEFAULT_TOP_N)

    def validate(self, attrs):
        context = attrs['context']
        if context == CONTEXT_PORT and not attrs.get('port'):
            raise serializers.ValidationError({'port': 'port is required when context=PORT.'})
        if context == CONTEXT_MOU and not attrs.get('mou'):
            raise serializers.ValidationError({'mou': 'mou is required when context=MOU.'})
        return attrs


def _merge_counter(into_counter, from_counter):
    for key, value in from_counter.items():
        into_counter[key] += value


def _aggregate_internal_counts(*, user, context, context_value_norm, cutoff_date, use_window):
    queryset = (
        Deficiency.objects.filter(
            is_deleted=False,
            inspection__is_deleted=False,
        )
        .select_related('inspection')
        .order_by('inspection__inspection_date', 'inspection_id', 'sequence_no')
    )
    queryset = _apply_user_access_scope(queryset, user)

    if use_window:
        queryset = queryset.filter(inspection__inspection_date__gte=cutoff_date)

    global_counts = defaultdict(int)
    context_counts = defaultdict(int)
    last_seen_by_def_code = {}
    invalid_rows = 0

    for deficiency in queryset.iterator():
        inspection = deficiency.inspection
        try:
            def_code = _normalize_def_code(deficiency.def_code_id or deficiency.def_code)
            if context == CONTEXT_PORT:
                context_value = _normalize_text(inspection.port_place, field_name='port')
            else:
                context_value = _normalize_text(inspection.mou_id, field_name='mou')
        except ValueError:
            invalid_rows += 1
            continue

        global_counts[def_code] += 1
        if context_value == context_value_norm:
            context_counts[def_code] += 1
            seen_date = inspection.inspection_date
            previous = last_seen_by_def_code.get(def_code)
            if seen_date and (previous is None or seen_date > previous):
                last_seen_by_def_code[def_code] = seen_date

    return {
        'global_counts': global_counts,
        'context_counts': context_counts,
        'last_seen_by_def_code': last_seen_by_def_code,
        'invalid_rows': invalid_rows,
    }


def _aggregate_opensource_counts(*, context, context_value_norm, cutoff_year, use_window):
    queryset = OpenSourceDeficiencyRecord.objects.all().order_by('year', 'id')
    if use_window:
        queryset = queryset.filter(year__gte=cutoff_year)

    global_counts = defaultdict(int)
    context_counts = defaultdict(int)
    invalid_rows = 0

    for row in queryset.iterator():
        try:
            def_code = _normalize_def_code(row.def_code_norm)
            if context == CONTEXT_PORT:
                context_value = _normalize_text(row.port_norm, field_name='port')
            else:
                context_value = _normalize_text(row.mou_norm, field_name='mou')
        except ValueError:
            invalid_rows += 1
            continue

        global_counts[def_code] += 1
        if context_value == context_value_norm:
            context_counts[def_code] += 1

    return {
        'global_counts': global_counts,
        'context_counts': context_counts,
        'invalid_rows': invalid_rows,
    }


class DefIntelPredictDefCodesView(APIView):
    """
    GET /api/psc/reports/defintel/predict-defcodes/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not can_access_defintel_reports(request.user):
            return Response(
                {
                    'error': 'FORBIDDEN',
                    'message': 'DefIntel prediction is available to Office users and vessel ranks Master/CO/CE/2E only.',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DefIntelPredictionQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': 'Invalid query parameters.',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        context = validated['context']
        window = validated['window']
        top_n = validated['top_n']
        raw_context_value = validated['port'] if context == CONTEXT_PORT else validated['mou']
        context_field_name = 'port' if context == CONTEXT_PORT else 'mou'

        try:
            context_value_norm = _normalize_text(raw_context_value, field_name=context_field_name)
        except ValueError as exc:
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cutoff_date = _shift_months_back(date.today(), 24)
        use_window = window == WINDOW_LAST_24_MONTHS
        alpha = int(getattr(settings, 'DEFINTEL_PREDICTION_ALPHA', DEFAULT_ALPHA))

        internal_counts = _aggregate_internal_counts(
            user=request.user,
            context=context,
            context_value_norm=context_value_norm,
            cutoff_date=cutoff_date,
            use_window=use_window,
        )
        opensource_counts = _aggregate_opensource_counts(
            context=context,
            context_value_norm=context_value_norm,
            cutoff_year=cutoff_date.year,
            use_window=use_window,
        )

        global_counts = defaultdict(int)
        context_counts = defaultdict(int)
        _merge_counter(global_counts, internal_counts['global_counts'])
        _merge_counter(global_counts, opensource_counts['global_counts'])
        _merge_counter(context_counts, internal_counts['context_counts'])
        _merge_counter(context_counts, opensource_counts['context_counts'])

        total_global = sum(global_counts.values())
        total_context = sum(context_counts.values())

        rows = []
        if total_global > 0 and total_context > 0:
            for def_code, count_context in context_counts.items():
                count_global = global_counts.get(def_code, 0)
                p_global = count_global / total_global
                probability = (count_context + alpha * p_global) / (total_context + alpha)
                last_seen = internal_counts['last_seen_by_def_code'].get(def_code)
                rows.append(
                    {
                        'def_code': def_code,
                        'probability': round(probability, 6),
                        'count_context': count_context,
                        'count_global': count_global,
                        'last_seen_date': last_seen.isoformat() if last_seen else None,
                    }
                )

        rows.sort(
            key=lambda row: (
                -row['probability'],
                -row['count_context'],
                -row['count_global'],
                row['def_code'],
            )
        )
        rows = rows[:top_n]

        response_payload = {
            'context': context,
            'context_value': context_value_norm,
            'window': window,
            'alpha': alpha,
            'top_n': top_n,
            'rows': rows,
        }
        if use_window:
            response_payload['window_fallback'] = (
                'LAST_24_MONTHS uses exact date filtering for internal data; '
                'OpenSource uses year >= cutoff_year because only year is stored.'
            )
            response_payload['window_cutoff_date'] = cutoff_date.isoformat()
            response_payload['window_cutoff_year'] = cutoff_date.year
        response_payload['invalid_rows_skipped'] = (
            internal_counts['invalid_rows'] + opensource_counts['invalid_rows']
        )

        return Response(
            {
                'data': response_payload,
                'message': 'DefIntel prediction generated successfully.',
            },
            status=status.HTTP_200_OK,
        )
