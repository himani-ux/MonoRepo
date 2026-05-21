from __future__ import annotations

from .base import BaseRepository


class PurchaseRepository(BaseRepository):
    table_name = "pur_requisition"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._table_columns_cache: dict[str, set[str]] = {}

    def table_exists(self) -> bool:
        return self.table_name in self.connection.introspection.table_names()

    def get_requisition(self, purchase_req_id: int) -> dict[str, object] | None:
        if not self.table_exists():
            return None

        rows = self.execute_query(self._build_requisition_query(), [purchase_req_id])
        if not rows:
            return None

        row = rows[0]
        return {
            "id": int(row["id"]),
            "status": row.get("status"),
            "is_archived": self._coerce_bool(row.get("is_archived")),
        }

    def _build_requisition_query(self) -> str:
        columns = self._get_table_columns(self.table_name)
        status_sql = "status AS status" if "status" in columns else "NULL AS status"
        if "is_archived" in columns:
            archived_sql = "is_archived AS is_archived"
        elif "archived_at" in columns:
            archived_sql = "CASE WHEN archived_at IS NULL THEN 0 ELSE 1 END AS is_archived"
        else:
            archived_sql = "0 AS is_archived"

        return (
            "SELECT\n"
            "    id,\n"
            f"    {status_sql},\n"
            f"    {archived_sql}\n"
            f"FROM {self.table_name}\n"
            "WHERE id = %s"
        )

    def _get_table_columns(self, table_name: str) -> set[str]:
        if table_name in self._table_columns_cache:
            return self._table_columns_cache[table_name]

        try:
            with self.connection.cursor() as cursor:
                description = self.connection.introspection.get_table_description(cursor, table_name)
        except Exception:
            columns: set[str] = set()
        else:
            columns = set()
            for column in description:
                if hasattr(column, "name"):
                    columns.add(str(column.name))
                else:
                    columns.add(str(column[0]))

        self._table_columns_cache[table_name] = columns
        return columns

    def _coerce_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value in (0, 1):
            return bool(value)
        return str(value).strip().lower() in {"true", "1", "yes"}
