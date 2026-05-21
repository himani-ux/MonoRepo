from __future__ import annotations

import unittest
from unittest.mock import patch

import django
from django.apps import apps

from apps.safety.repositories import BaseRepository
from apps.safety.repositories.exceptions import (
    SPDeadlockError,
    SPExecutionError,
    SPParameterError,
    SPTimeoutError,
)


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-3-repository-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )

    if not apps.ready:
        django.setup()


class FakeCursor:
    def __init__(self, *, responses=None, description=None, rows=None) -> None:
        self.responses = list(responses or [None])
        self.description = description
        self.rows = list(rows or [])
        self.execute_calls: list[tuple[str, object]] = []
        self.timeout = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def execute(self, statement, params=None) -> None:
        self.execute_calls.append((statement, params))
        response = self.responses.pop(0) if self.responses else None
        if isinstance(response, Exception):
            raise response

    def fetchall(self):
        return list(self.rows)


class FakeConnection:
    def __init__(self, cursors) -> None:
        self.cursors = list(cursors)
        self.cursor_calls = 0

    def cursor(self):
        cursor = self.cursors[self.cursor_calls]
        self.cursor_calls += 1
        return cursor


class BaseRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def test_execute_sp_returns_dict_rows(self) -> None:
        cursor = FakeCursor(
            description=[("id",), ("name",)],
            rows=[(1, "alpha"), (2, "beta")],
        )
        connection = FakeConnection([cursor])
        repository = BaseRepository()

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            result = repository.execute_sp("dbo.usp_SafetyList", {"vessel_id": 9, "state": "OPEN"})

        self.assertEqual(
            result,
            [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}],
        )
        self.assertEqual(
            cursor.execute_calls,
            [("EXEC dbo.usp_SafetyList @vessel_id = %s, @state = %s", (9, "OPEN"))],
        )
        self.assertEqual(cursor.timeout, 30)

    def test_execute_query_retries_deadlock_then_succeeds(self) -> None:
        deadlock_cursor = FakeCursor(responses=[RuntimeError("Transaction deadlock 1205")])
        success_cursor = FakeCursor(description=[("count",)], rows=[(3,)])
        connection = FakeConnection([deadlock_cursor, success_cursor])
        repository = BaseRepository(deadlock_retry_attempts=3)

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            with self.assertLogs("apps.safety.repositories.base", level="WARNING") as captured:
                result = repository.execute_query("SELECT COUNT(*) AS count FROM vims_safety_incident")

        self.assertEqual(result, [{"count": 3}])
        self.assertEqual(connection.cursor_calls, 2)
        self.assertEqual(len(captured.records), 1)

    def test_execute_query_raises_timeout_error(self) -> None:
        timeout_cursor = FakeCursor(responses=[RuntimeError("Query timeout expired HYT00")])
        connection = FakeConnection([timeout_cursor])
        repository = BaseRepository()

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            with self.assertRaises(SPTimeoutError):
                repository.execute_query("SELECT 1")

    def test_execute_query_raises_parameter_error_for_string_params(self) -> None:
        repository = BaseRepository()

        with self.assertRaises(SPParameterError):
            repository.execute_query("SELECT 1 WHERE name = %s", params="bad")

    def test_execute_sp_raises_parameter_error_for_invalid_identifier(self) -> None:
        repository = BaseRepository()

        with self.assertRaises(SPParameterError):
            repository.execute_sp("dbo.usp_SafetyList; DROP TABLE master_role")

    def test_execute_scalar_returns_first_value(self) -> None:
        cursor = FakeCursor(description=[("next_id",), ("ignored",)], rows=[(41, "x")])
        connection = FakeConnection([cursor])
        repository = BaseRepository()

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            value = repository.execute_scalar("SELECT 41 AS next_id, 'x' AS ignored")

        self.assertEqual(value, 41)

    def test_execute_query_raises_deadlock_error_after_last_retry(self) -> None:
        connection = FakeConnection(
            [
                FakeCursor(responses=[RuntimeError("deadlock victim")]),
                FakeCursor(responses=[RuntimeError("deadlock victim")]),
            ]
        )
        repository = BaseRepository(deadlock_retry_attempts=2)

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            with self.assertLogs("apps.safety.repositories.base", level="WARNING") as captured:
                with self.assertRaises(SPDeadlockError):
                    repository.execute_query("SELECT 1")

        self.assertEqual(len(captured.records), 1)

    def test_connection_property_reuses_default_alias(self) -> None:
        connection = object()
        repository = BaseRepository()

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            self.assertIs(repository.connection, connection)
            self.assertIs(repository.connection, connection)

    def test_execute_query_wraps_unexpected_errors(self) -> None:
        failing_cursor = FakeCursor(responses=[RuntimeError("syntax error near FROM")])
        connection = FakeConnection([failing_cursor])
        repository = BaseRepository()

        with patch("apps.safety.repositories.base.connections", {"default": connection}):
            with self.assertRaises(SPExecutionError):
                repository.execute_query("SELECT FROM broken")
