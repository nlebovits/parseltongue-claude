"""Tests for the Parseltongue MCP server."""

from __future__ import annotations

import json

import pytest

from parseltongue_claude.server import (
    _sessions,
    parseltongue_check_consistency,
    parseltongue_clear_session,
    parseltongue_create_session,
    parseltongue_get_state,
    parseltongue_list_sessions,
    parseltongue_load_dsl,
    parseltongue_register_document,
)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before and after each test."""
    _sessions.clear()
    yield
    _sessions.clear()


class TestCreateSession:
    """Tests for session creation."""

    def test_create_new_session(self):
        """Should create a new session."""
        result = json.loads(parseltongue_create_session("test-session"))

        assert result["status"] == "created"
        assert result["session_id"] == "test-session"
        assert "test-session" in _sessions

    def test_create_existing_session(self):
        """Should return exists status for duplicate session."""
        parseltongue_create_session("test-session")
        result = json.loads(parseltongue_create_session("test-session"))

        assert result["status"] == "exists"
        assert "already exists" in result["message"]


class TestRegisterDocument:
    """Tests for document registration."""

    def test_register_document(self):
        """Should register a document and return stats."""
        parseltongue_create_session("test")
        content = "The revenue was $42 million in Q3."

        result = json.loads(parseltongue_register_document("test", "report", content))

        assert result["status"] == "registered"
        assert result["document"] == "report"
        assert result["chars"] == len(content)
        assert result["lines"] == 1

    def test_register_multiline_document(self):
        """Should count lines correctly."""
        parseltongue_create_session("test")
        content = "Line 1\nLine 2\nLine 3"

        result = json.loads(parseltongue_register_document("test", "doc", content))

        assert result["lines"] == 3


class TestLoadDsl:
    """Tests for DSL loading and verification."""

    def test_load_valid_fact_with_verified_quote(self):
        """Should verify quotes that exist in the document."""
        parseltongue_create_session("test")
        parseltongue_register_document("test", "report", "The revenue was $42 million.")

        dsl = """
        (fact revenue 42000000
            :evidence (evidence "report"
                :quotes ("The revenue was $42 million")
                :explanation "Q3 revenue"))
        """

        result = json.loads(parseltongue_load_dsl("test", dsl))

        assert result["status"] == "loaded"
        assert result["facts_count"] == 1
        assert result["verified_count"] == 1
        assert result["unverified_count"] == 0

    def test_load_fact_with_hallucinated_quote(self):
        """Should flag quotes that don't exist in the document."""
        parseltongue_create_session("test")
        parseltongue_register_document("test", "report", "The revenue was $42 million.")

        dsl = """
        (fact fake-claim 999
            :evidence (evidence "report"
                :quotes ("This quote does not exist")
                :explanation "Fabricated"))
        """

        result = json.loads(parseltongue_load_dsl("test", dsl))

        assert result["status"] == "loaded"
        assert result["unverified_count"] == 1
        assert result["unverified"][0]["symbol"] == "fake-claim"
        assert result["unverified"][0]["reason"] == "quote_mismatch"

    def test_load_invalid_dsl(self):
        """Should return parse error for invalid DSL."""
        parseltongue_create_session("test")

        result = json.loads(parseltongue_load_dsl("test", "not valid dsl"))

        assert result["status"] == "parse_error"
        assert "error" in result


class TestGetState:
    """Tests for session state retrieval."""

    def test_get_empty_state(self):
        """Should return empty state for new session."""
        parseltongue_create_session("test")

        result = json.loads(parseltongue_get_state("test"))

        assert result["session_id"] == "test"
        assert result["facts_count"] == 0
        assert result["theorems_count"] == 0

    def test_get_state_with_facts(self):
        """Should return facts after loading DSL."""
        parseltongue_create_session("test")
        parseltongue_register_document("test", "doc", "Value is 42.")
        parseltongue_load_dsl(
            "test", '(fact value 42 :evidence (evidence "doc" :quotes ("Value is 42")))'
        )

        result = json.loads(parseltongue_get_state("test"))

        assert result["facts_count"] == 1
        assert "value" in result["facts"]


class TestListSessions:
    """Tests for listing sessions."""

    def test_list_empty(self):
        """Should return empty list when no sessions."""
        result = json.loads(parseltongue_list_sessions())

        assert result["count"] == 0
        assert result["sessions"] == []

    def test_list_multiple_sessions(self):
        """Should list all sessions."""
        parseltongue_create_session("session-1")
        parseltongue_create_session("session-2")

        result = json.loads(parseltongue_list_sessions())

        assert result["count"] == 2
        session_ids = [s["session_id"] for s in result["sessions"]]
        assert "session-1" in session_ids
        assert "session-2" in session_ids


class TestClearSession:
    """Tests for clearing sessions."""

    def test_clear_existing_session(self):
        """Should clear session state."""
        parseltongue_create_session("test")
        parseltongue_register_document("test", "doc", "content")

        result = json.loads(parseltongue_clear_session("test"))

        assert result["status"] == "cleared"
        # Session still exists but is empty
        state = json.loads(parseltongue_get_state("test"))
        assert state["facts_count"] == 0

    def test_clear_nonexistent_session(self):
        """Should return not_found for missing session."""
        result = json.loads(parseltongue_clear_session("nonexistent"))

        assert result["status"] == "not_found"


class TestCheckConsistency:
    """Tests for consistency checking."""

    def test_check_empty_session(self):
        """Should return checked status for empty session."""
        parseltongue_create_session("test")

        result = json.loads(parseltongue_check_consistency("test"))

        assert result["status"] == "checked"
