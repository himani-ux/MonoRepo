"""Audit rule-book clause master API."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import MasterRcaTemplate
from apps.inspection.audit.services.finding import RULE_BOOK_MASTER_MODELS


class AuditClauseMasterView(APIView):
    """GET /api/audit/masters/clauses/{book}/ for the finding-create modal."""

    permission_classes = [IsAuthenticated]

    def get(self, request, book):
        rule_book_type = str(book or "").strip().upper()
        master_model = RULE_BOOK_MASTER_MODELS.get(rule_book_type)
        if master_model is None:
            return Response(
                {
                    "error": "UNKNOWN_RULE_BOOK",
                    "message": "No seeded clause master exists for this rule book.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        rows = [_master_row_payload(row, rule_book_type) for row in master_model.objects.all().order_by("id")]
        return Response({"data": {"rule_book_type": rule_book_type, "clauses": rows}})


class AuditRcaTemplateMasterView(APIView):
    """GET /api/audit/masters/rca-templates/ for the NC closure wizard."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = str(request.query_params.get("category") or "").strip().upper()
        rows = MasterRcaTemplate.objects.filter(is_active=True)
        if category:
            rows = rows.filter(category=category)
        rows = rows.order_by("category", "title", "id")
        return Response(
            {
                "data": {
                    "category": category,
                    "templates": [_rca_template_payload(row) for row in rows],
                }
            }
        )


def _master_row_payload(row, rule_book_type: str) -> dict[str, str]:
    code = _row_code(row, rule_book_type)
    return {
        "id": str(row.id),
        "code": code,
        "title": _row_title(row, rule_book_type),
        "code_version": str(getattr(row, "code_version", "") or ""),
    }


def _row_code(row, rule_book_type: str) -> str:
    if rule_book_type == "ISM":
        return row.clause_no
    if rule_book_type == "ISPS":
        return row.section_no
    if rule_book_type == "MLC":
        return row.standard_a_code or row.regulation_no or row.title_no
    if rule_book_type == "SOLAS":
        return " ".join(part for part in (row.chapter_no, row.regulation_no) if part)
    if rule_book_type == "STCW":
        return row.section_no
    if rule_book_type == "MARPOL":
        return " ".join(part for part in (row.annex_no, row.regulation_no) if part)
    if rule_book_type == "COLREG":
        return row.rule_no
    if rule_book_type == "KSM_SMS":
        return row.chapter_code
    return rule_book_type


def _row_title(row, rule_book_type: str) -> str:
    for attr_name in ("clause_text", "section_title", "title_text", "title", "chapter_name"):
        value = str(getattr(row, attr_name, "") or "").strip()
        if value:
            return value
    return _row_code(row, rule_book_type)


def _rca_template_payload(row: MasterRcaTemplate) -> dict[str, str]:
    return {
        "id": str(row.id),
        "category": row.category,
        "title": row.title,
        "template_text": row.template_text,
        "example_evidence_hint": row.example_evidence_hint or "",
        "applicable_def_categories": row.applicable_def_categories or "",
        "code_version": row.code_version or "",
    }
