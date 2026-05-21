from __future__ import annotations

from collections.abc import Mapping, Sequence
import logging
import re

from django.db import connections

from .exceptions import SPDeadlockError, SPExecutionError, SPParameterError, SPTimeoutError


logger = logging.getLogger(__name__)
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_\.\[\]]+$")


class BaseRepository:
    """Minimal repository wrapper for Safety database access."""

    def __init__(
        self,
        *,
        connection_alias: str = "default",
        deadlock_retry_attempts: int = 3,
        timeout_seconds: int = 30,
    ) -> None:
        self.connection_alias = connection_alias
        self.deadlock_retry_attempts = deadlock_retry_attempts
        self.timeout_seconds = timeout_seconds

    @property
    def connection(self):
        return connections[self.connection_alias]

    def execute_sp(self, sp_name: str, params: Mapping[str, object] | None = None) -> list[dict]:
        validated_name = self._validate_identifier(sp_name, label="stored procedure")
        normalized_params = self._normalize_sp_params(params)
        statement, values = self._build_sp_statement(validated_name, normalized_params)
        return self._execute(statement, values, timeout_seconds=self.timeout_seconds)

    def execute_query(
        self,
        sql: str,
        params: Mapping[str, object] | Sequence[object] | None = None,
    ) -> list[dict]:
        validated_sql = self._validate_sql(sql)
        normalized_params = self._normalize_query_params(params)
        return self._execute(validated_sql, normalized_params, timeout_seconds=self.timeout_seconds)

    def execute_scalar(
        self,
        sql: str,
        params: Mapping[str, object] | Sequence[object] | None = None,
    ):
        rows = self.execute_query(sql, params=params)
        if not rows:
            return None

        first_row = rows[0]
        return next(iter(first_row.values())) if first_row else None

    def _execute(self, statement: str, params, *, timeout_seconds: int) -> list[dict]:
        for attempt in range(1, self.deadlock_retry_attempts + 1):
            try:
                with self.connection.cursor() as cursor:
                    self._apply_timeout(cursor, timeout_seconds)
                    if params is None:
                        cursor.execute(statement)
                    else:
                        cursor.execute(statement, params)

                    if not cursor.description:
                        return []

                    return self._rows_to_dicts(cursor.description, cursor.fetchall())
            except Exception as exc:  # pragma: no cover - exercised by unit tests
                if self._is_deadlock_error(exc):
                    if attempt < self.deadlock_retry_attempts:
                        logger.warning(
                            "Safety repository deadlock detected; retrying %s/%s",
                            attempt,
                            self.deadlock_retry_attempts,
                        )
                        continue
                    raise SPDeadlockError(
                        "Database deadlock persisted after retry attempts.",
                        statement=statement,
                        params=params,
                        original_exception=exc,
                    ) from exc

                if self._is_timeout_error(exc):
                    raise SPTimeoutError(
                        "Database operation timed out.",
                        statement=statement,
                        params=params,
                        original_exception=exc,
                    ) from exc

                raise SPExecutionError(
                    "Database operation failed.",
                    statement=statement,
                    params=params,
                    original_exception=exc,
                ) from exc

        raise SPExecutionError("Database operation failed without executing.")

    def _apply_timeout(self, cursor, timeout_seconds: int) -> None:
        if hasattr(cursor, "timeout"):
            cursor.timeout = timeout_seconds

    def _build_sp_statement(
        self,
        sp_name: str,
        params: Mapping[str, object],
    ) -> tuple[str, Sequence[object] | None]:
        if not params:
            return f"EXEC {sp_name}", None

        assignments: list[str] = []
        values: list[object] = []
        for key, value in params.items():
            param_name = self._validate_identifier(key, label="stored procedure parameter")
            assignments.append(f"@{param_name} = %s")
            values.append(value)

        return f"EXEC {sp_name} {', '.join(assignments)}", tuple(values)

    def _normalize_sp_params(self, params: Mapping[str, object] | None) -> Mapping[str, object]:
        if params is None:
            return {}
        if not isinstance(params, Mapping):
            raise SPParameterError("Stored procedure parameters must be a mapping.", params=params)
        return dict(params)

    def _normalize_query_params(
        self,
        params: Mapping[str, object] | Sequence[object] | None,
    ):
        if params is None:
            return None
        if isinstance(params, Mapping):
            return dict(params)
        if isinstance(params, (str, bytes, bytearray)):
            raise SPParameterError("Query parameters must be a mapping or sequence.", params=params)
        if isinstance(params, Sequence):
            return tuple(params)
        raise SPParameterError("Query parameters must be a mapping or sequence.", params=params)

    def _validate_identifier(self, value: str, *, label: str) -> str:
        if not isinstance(value, str):
            raise SPParameterError(f"{label.title()} name must be a string.", params=value)

        normalized = value.strip()
        if not normalized:
            raise SPParameterError(f"{label.title()} name cannot be empty.", params=value)

        if not _VALID_IDENTIFIER_RE.fullmatch(normalized):
            raise SPParameterError(
                f"{label.title()} name contains unsupported characters.",
                params=value,
            )
        return normalized

    def _validate_sql(self, sql: str) -> str:
        if not isinstance(sql, str):
            raise SPParameterError("SQL statement must be a string.", params=sql)

        normalized = sql.strip()
        if not normalized:
            raise SPParameterError("SQL statement cannot be empty.", params=sql)
        return normalized

    def _rows_to_dicts(self, description, rows) -> list[dict]:
        column_names = [column[0] for column in description]
        return [dict(zip(column_names, row)) for row in rows]

    def _is_deadlock_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "deadlock" in text or "1205" in text or "40001" in text

    def _is_timeout_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "timeout" in text or "timed out" in text or "hyt00" in text or "hyt01" in text
