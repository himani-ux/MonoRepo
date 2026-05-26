from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from django.db import connections
from django.db.models import Case, IntegerField, Q, Value, When


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[.\-][A-Za-z0-9]+)*")


class FtsUnavailableError(RuntimeError):
    """Raised when SQL Server FTS was selected but is not ready on the current connection."""


@dataclass(frozen=True)
class FtsSearchHit:
    pk: int
    rank: float


class SafetyFtsEngine:
    MIN_DESCRIPTION_SIMILARITY = 0.45

    def __init__(self, *, connection_alias: str = "default") -> None:
        self.connection_alias = connection_alias

    @property
    def connection(self):
        return connections[self.connection_alias]

    def supports_sql_server_fts(self) -> bool:
        return self.connection.vendor == "microsoft"

    def build_sql_server_contains_query(self, query: str) -> str:
        tokens = self._tokenize(query, lowercase=False)
        if not tokens:
            return ""
        return " AND ".join(f'"{token}*"' for token in tokens)

    def description_similarity(self, left: str | None, right: str | None) -> float:
        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)
        if not left_tokens or not right_tokens:
            return 0.0

        left_text = " ".join(left_tokens)
        right_text = " ".join(right_tokens)
        sequence_ratio = SequenceMatcher(None, left_text, right_text).ratio()

        left_set = set(left_tokens)
        right_set = set(right_tokens)
        overlap = left_set & right_set
        jaccard = len(overlap) / max(len(left_set | right_set), 1)
        containment = len(overlap) / max(min(len(left_set), len(right_set)), 1)
        return max(sequence_ratio, (jaccard + containment) / 2)

    def descriptions_are_similar(
        self,
        left: str | None,
        right: str | None,
        *,
        threshold: float | None = None,
    ) -> bool:
        effective_threshold = threshold or self.MIN_DESCRIPTION_SIMILARITY
        return self.description_similarity(left, right) >= effective_threshold

    def rank_queryset_portable(
        self,
        queryset,
        *,
        query: str,
        identifier_fields: tuple[str, ...],
        text_fields: tuple[str, ...],
        related_identifier_fields: tuple[str, ...] = (),
        ordering: tuple[str, ...],
    ):
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return queryset.annotate(match_rank=Value(0, output_field=IntegerField())).order_by(*ordering)

        search_filter = Q()
        for field_name in identifier_fields + related_identifier_fields:
            search_filter |= Q(**{f"{field_name}__icontains": normalized_query})
        for field_name in text_fields:
            search_filter |= Q(**{f"{field_name}__icontains": normalized_query})

        rank_conditions: list[When] = []
        rank_index = 0
        for field_name in identifier_fields + related_identifier_fields:
            rank_conditions.append(When(**{field_name: normalized_query}, then=Value(rank_index)))
            rank_index += 1
            rank_conditions.append(When(**{f"{field_name}__istartswith": normalized_query}, then=Value(rank_index)))
            rank_index += 1
        for field_name in text_fields:
            rank_conditions.append(When(**{f"{field_name}__istartswith": normalized_query}, then=Value(rank_index)))
            rank_index += 1

        return (
            queryset.filter(search_filter)
            .annotate(
                match_rank=Case(
                    *rank_conditions,
                    default=Value(rank_index),
                    output_field=IntegerField(),
                )
            )
            .distinct()
            .order_by("match_rank", *ordering)
        )

    def search_sql_server_primary_keys(
        self,
        *,
        query: str,
        source_table: str,
        text_columns: Sequence[str],
        identifier_columns: Sequence[str],
        base_where_sql: str,
        base_where_params: Sequence[object],
        base_join_sql: str = "",
        additional_match_clauses: Sequence[tuple[str, Sequence[object], float]] = (),
        limit: int = 10,
    ) -> list[int]:
        if not self.supports_sql_server_fts():
            raise FtsUnavailableError("SQL Server FTS is only available on Microsoft SQL Server connections.")

        contains_query = self.build_sql_server_contains_query(query)
        if not contains_query:
            return []

        self._assert_sql_server_fts_ready(source_table)

        unions: list[str] = []
        params: list[object] = []
        limit = max(int(limit), 1)

        if text_columns:
            column_list = ", ".join(f"[{column_name}]" for column_name in text_columns)
            unions.append(
                f"""
                SELECT DISTINCT src.id, CAST(ft.[RANK] AS FLOAT) + 1000.0 AS rank
                FROM base
                JOIN dbo.{source_table} src ON src.id = base.id
                JOIN CONTAINSTABLE(dbo.{source_table}, ({column_list}), %s) ft
                  ON src.id = ft.[KEY]
                """
            )
            params.append(contains_query)

        for column_name in identifier_columns:
            unions.append(
                f"""
                SELECT DISTINCT src.id, 4500.0 AS rank
                FROM base
                JOIN dbo.{source_table} src ON src.id = base.id
                WHERE src.[{column_name}] = %s
                """
            )
            params.append(str(query))
            unions.append(
                f"""
                SELECT DISTINCT src.id, 3500.0 AS rank
                FROM base
                JOIN dbo.{source_table} src ON src.id = base.id
                WHERE src.[{column_name}] LIKE %s
                """
            )
            params.append(f"{query}%")

        for clause_sql, clause_params, clause_rank in additional_match_clauses:
            unions.append(
                f"""
                SELECT DISTINCT src.id, {float(clause_rank)} AS rank
                FROM base
                JOIN dbo.{source_table} src ON src.id = base.id
                WHERE {clause_sql}
                """
            )
            params.extend(list(clause_params))

        if not unions:
            return []

        sql = f"""
        WITH base AS (
            SELECT DISTINCT src.id
            FROM dbo.{source_table} src
            {base_join_sql}
            WHERE {base_where_sql}
        )
        SELECT TOP {limit} ranked.id
        FROM (
            {" UNION ALL ".join(unions)}
        ) ranked
        GROUP BY ranked.id
        ORDER BY MAX(ranked.rank) DESC, ranked.id DESC
        """

        with self.connection.cursor() as cursor:
            cursor.execute(sql, [*base_where_params, *params])
            rows = cursor.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def order_records(records: Sequence[object], primary_keys: Sequence[object]) -> list[object]:
        order_map = {str(primary_key): index for index, primary_key in enumerate(primary_keys)}
        return sorted(
            records,
            key=lambda record: order_map.get(str(getattr(record, "pk", "")), len(order_map)),
        )

    def _assert_sql_server_fts_ready(self, source_table: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT FULLTEXTSERVICEPROPERTY('IsFullTextInstalled')")
            installed_row = cursor.fetchone()
            installed = int(installed_row[0] or 0) if installed_row else 0
            if installed != 1:
                raise FtsUnavailableError("SQL Server Full-Text Search is not installed on this server.")

            cursor.execute(
                """
                SELECT 1
                FROM sys.fulltext_indexes
                WHERE object_id = OBJECT_ID(%s)
                """,
                [f"dbo.{source_table}"],
            )
            if cursor.fetchone() is None:
                raise FtsUnavailableError(f"Full-text index missing for dbo.{source_table}.")

    @staticmethod
    def _tokenize(value: str | None, *, lowercase: bool = True) -> list[str]:
        tokens = [match.group(0) for match in _TOKEN_RE.finditer(str(value or ""))]
        if lowercase:
            return [token.lower() for token in tokens]
        return tokens
