"""Integration tests for the Parseltongue MCP server.

These tests spawn the actual MCP server as a subprocess and communicate
over stdio using the JSON-RPC protocol.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

import pytest


class MCPClient:
    """Simple MCP client for testing."""

    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.request_id = 0

    def start(self):
        """Start the MCP server subprocess."""
        self.process = subprocess.Popen(
            [sys.executable, "-m", "parseltongue_claude.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def stop(self):
        """Stop the MCP server subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

    def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict:
        """Send a JSON-RPC request and return the response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP server not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }

        # Send request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"No response from server. stderr: {stderr}")

        return json.loads(response_line)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict | str:
        """Call an MCP tool and return the parsed result."""
        response = self.send_request("tools/call", {"name": name, "arguments": arguments})

        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")

        # Extract content from MCP response
        result = response.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            text = content[0]["text"]
            # Try to parse as JSON, fall back to raw text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return result


@pytest.fixture
def mcp_client():
    """Fixture that provides a running MCP client."""
    client = MCPClient()
    client.start()
    yield client
    client.stop()


class TestMCPProtocol:
    """Test MCP protocol compliance."""

    def test_initialize_handshake(self, mcp_client: MCPClient):
        """Server should respond to initialize request."""
        response = mcp_client.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        assert "result" in response
        assert "protocolVersion" in response["result"]
        assert "serverInfo" in response["result"]
        assert response["result"]["serverInfo"]["name"] == "parseltongue"

    def test_list_tools(self, mcp_client: MCPClient):
        """Server should list available tools."""
        # Initialize first
        mcp_client.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        response = mcp_client.send_request("tools/list")

        assert "result" in response
        tools = response["result"].get("tools", [])
        tool_names = [t["name"] for t in tools]

        # Verify all expected tools are present
        expected_tools = [
            "parseltongue_create_session",
            "parseltongue_register_document",
            "parseltongue_load_dsl",
            "parseltongue_check_consistency",
            "parseltongue_get_state",
            "parseltongue_query",
            "parseltongue_list_sessions",
            "parseltongue_clear_session",
            "parseltongue_dsl_reference",
        ]
        for tool in expected_tools:
            assert tool in tool_names, f"Missing tool: {tool}"


class TestMCPToolCalls:
    """Test tool calls over MCP protocol."""

    @pytest.fixture(autouse=True)
    def setup_client(self, mcp_client: MCPClient):
        """Initialize the MCP connection before each test."""
        mcp_client.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )
        self.client = mcp_client

    def test_create_session_via_mcp(self):
        """Should create session through MCP tool call."""
        result = self.client.call_tool(
            "parseltongue_create_session", {"session_id": "integration-test"}
        )

        assert result["status"] == "created"
        assert result["session_id"] == "integration-test"

    def test_full_verification_workflow(self):
        """Test complete document verification workflow over MCP."""
        # 1. Create session
        result = self.client.call_tool(
            "parseltongue_create_session", {"session_id": "workflow-test"}
        )
        assert result["status"] == "created"

        # 2. Register document
        result = self.client.call_tool(
            "parseltongue_register_document",
            {
                "session_id": "workflow-test",
                "name": "report",
                "content": "Q3 revenue reached $42 million, exceeding the $40 million target.",
            },
        )
        assert result["status"] == "registered"

        # 3. Load DSL with verified facts
        dsl = """
        (fact revenue 42000000
            :evidence (evidence "report"
                :quotes ("Q3 revenue reached $42 million")
                :explanation "Quarterly revenue"))

        (fact target 40000000
            :evidence (evidence "report"
                :quotes ("exceeding the $40 million target")
                :explanation "Revenue target"))
        """
        result = self.client.call_tool(
            "parseltongue_load_dsl", {"session_id": "workflow-test", "dsl_source": dsl}
        )
        assert result["status"] == "loaded"
        assert result["facts_count"] == 2
        assert result["verified_count"] == 2
        assert result["unverified_count"] == 0

        # 4. Check consistency
        result = self.client.call_tool(
            "parseltongue_check_consistency", {"session_id": "workflow-test"}
        )
        assert result["status"] == "checked"

        # 5. Get state
        result = self.client.call_tool("parseltongue_get_state", {"session_id": "workflow-test"})
        assert result["facts_count"] == 2
        assert "revenue" in result["facts"]
        assert "target" in result["facts"]

    def test_hallucination_detection_via_mcp(self):
        """Verify hallucination detection works over MCP protocol."""
        # Setup
        self.client.call_tool("parseltongue_create_session", {"session_id": "hallucination-test"})
        self.client.call_tool(
            "parseltongue_register_document",
            {
                "session_id": "hallucination-test",
                "name": "doc",
                "content": "The actual text says something completely different.",
            },
        )

        # Load DSL with fabricated quote
        dsl = """
        (fact fabricated 999
            :evidence (evidence "doc"
                :quotes ("This quote was never in the document")
                :explanation "Made up claim"))
        """
        result = self.client.call_tool(
            "parseltongue_load_dsl", {"session_id": "hallucination-test", "dsl_source": dsl}
        )

        # Should detect the hallucination
        assert result["status"] == "loaded"
        assert result["unverified_count"] == 1
        assert result["unverified"][0]["symbol"] == "fabricated"
        assert result["unverified"][0]["reason"] == "quote_mismatch"

    def test_session_isolation(self):
        """Sessions should be isolated from each other."""
        # Create two sessions
        self.client.call_tool("parseltongue_create_session", {"session_id": "session-a"})
        self.client.call_tool("parseltongue_create_session", {"session_id": "session-b"})

        # Register doc in session-a only
        self.client.call_tool(
            "parseltongue_register_document",
            {"session_id": "session-a", "name": "doc", "content": "Session A content."},
        )

        # Load fact in session-a
        self.client.call_tool(
            "parseltongue_load_dsl",
            {
                "session_id": "session-a",
                "dsl_source": '(fact item 1 :evidence (evidence "doc" :quotes ("Session A")))',
            },
        )

        # Verify session-a has the fact
        result_a = self.client.call_tool("parseltongue_get_state", {"session_id": "session-a"})
        assert result_a["facts_count"] == 1

        # Verify session-b is empty
        result_b = self.client.call_tool("parseltongue_get_state", {"session_id": "session-b"})
        assert result_b["facts_count"] == 0

    def test_list_sessions_via_mcp(self):
        """Should list all sessions through MCP."""
        # Create multiple sessions
        self.client.call_tool("parseltongue_create_session", {"session_id": "list-test-1"})
        self.client.call_tool("parseltongue_create_session", {"session_id": "list-test-2"})

        result = self.client.call_tool("parseltongue_list_sessions", {})

        assert result["count"] >= 2
        session_ids = [s["session_id"] for s in result["sessions"]]
        assert "list-test-1" in session_ids
        assert "list-test-2" in session_ids

    def test_clear_session_via_mcp(self):
        """Should clear session state through MCP."""
        # Setup session with data
        self.client.call_tool("parseltongue_create_session", {"session_id": "clear-test"})
        self.client.call_tool(
            "parseltongue_register_document",
            {"session_id": "clear-test", "name": "doc", "content": "Test content."},
        )

        # Clear it
        result = self.client.call_tool("parseltongue_clear_session", {"session_id": "clear-test"})
        assert result["status"] == "cleared"

        # Verify it's empty
        state = self.client.call_tool("parseltongue_get_state", {"session_id": "clear-test"})
        assert state["facts_count"] == 0

    def test_dsl_reference_via_mcp(self):
        """Should return DSL reference documentation."""
        result = self.client.call_tool("parseltongue_dsl_reference", {})

        # Returns raw markdown documentation
        assert isinstance(result, str)
        assert len(result) > 100  # Should have substantial content
        assert "Parseltongue" in result or "fact" in result.lower()
