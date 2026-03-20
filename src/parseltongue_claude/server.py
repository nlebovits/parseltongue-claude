"""
Parseltongue MCP Server — symbolic verification engine for Claude Code.

Exposes Parseltongue's core engine as MCP tools, enabling Claude Code to:
1. Register source documents for evidence grounding
2. Load DSL (facts, axioms, derives, diffs) and verify consistency
3. Check quote verification status (catch hallucinations)
4. Query the formal system

This inverts the typical Parseltongue architecture: instead of Parseltongue
calling an LLM API, Claude Code (the LLM) calls Parseltongue for verification.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from parseltongue.core import System, load_source

# Initialize FastMCP server
mcp = FastMCP("parseltongue")

# Session storage: maps session_id -> System instance
_sessions: dict[str, System] = {}


def get_session(session_id: str) -> System:
    """Get or create a session."""
    if session_id not in _sessions:
        _sessions[session_id] = System(overridable=True)
    return _sessions[session_id]


# ============================================================================
# MCP Tools
# ============================================================================


@mcp.tool()
def parseltongue_create_session(session_id: str) -> str:
    """Create a new Parseltongue verification session.

    Args:
        session_id: Unique identifier for this session (e.g., 'sec-filing-review')

    Returns:
        JSON with session creation status
    """
    if session_id in _sessions:
        return json.dumps({"status": "exists", "session_id": session_id, "message": "Session already exists"})

    _sessions[session_id] = System(overridable=True)
    return json.dumps({"status": "created", "session_id": session_id})


@mcp.tool()
def parseltongue_register_document(session_id: str, name: str, content: str) -> str:
    """Register a source document for evidence grounding.

    Facts extracted from this document can cite it with :evidence blocks.

    Args:
        session_id: Session ID
        name: Document name (referenced in :evidence blocks)
        content: Document text content

    Returns:
        JSON with registration status
    """
    system = get_session(session_id)
    system.register_document(name, content)
    return json.dumps({
        "status": "registered",
        "document": name,
        "chars": len(content),
        "lines": content.count("\n") + 1,
    })


@mcp.tool()
def parseltongue_load_dsl(session_id: str, dsl_source: str) -> str:
    """Load Parseltongue DSL into the session.

    Parses facts, axioms, defterms, derives, and diffs.
    Returns verification status including any quote mismatches (hallucinations).

    Args:
        session_id: Session ID
        dsl_source: Parseltongue DSL source code

    Returns:
        JSON with parse status and verification results
    """
    system = get_session(session_id)

    try:
        load_source(system, dsl_source)
    except Exception as e:
        return json.dumps({"status": "parse_error", "error": str(e)})

    # Get verification status (facts/theorems are dicts)
    facts = system.facts
    theorems = system.theorems

    # Check for unverified quotes (hallucinations)
    unverified = []
    verified = []
    for name, fact in facts.items():
        origin = getattr(fact, "origin", None)
        if origin and hasattr(origin, "verified"):
            if origin.verified:
                verified.append(name)
            else:
                unverified.append({
                    "symbol": name,
                    "reason": "quote_mismatch",
                    "quotes": getattr(origin, "quotes", []),
                })

    return json.dumps({
        "status": "loaded",
        "facts_count": len(facts),
        "theorems_count": len(theorems),
        "verified_count": len(verified),
        "unverified_count": len(unverified),
        "unverified": unverified[:10],
        "has_more_unverified": len(unverified) > 10,
    })


@mcp.tool()
def parseltongue_check_consistency(session_id: str) -> str:
    """Run full consistency check on the session.

    Returns detailed report of verified claims, unverified claims (hallucinations),
    and logical inconsistencies.

    Args:
        session_id: Session ID

    Returns:
        JSON with consistency check results
    """
    system = get_session(session_id)

    try:
        report = system.consistency()
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

    if isinstance(report, dict):
        return json.dumps({"status": "checked", **report})

    return json.dumps({
        "status": "checked",
        "consistent": getattr(report, "consistent", True),
        "issues": getattr(report, "issues", []),
        "unverified": getattr(report, "unverified", []),
        "summary": str(report),
    })


@mcp.tool()
def parseltongue_get_state(session_id: str) -> str:
    """Get current state of the session.

    Returns facts, derives, axioms, and their verification status.

    Args:
        session_id: Session ID

    Returns:
        JSON with session state
    """
    system = get_session(session_id)

    facts = system.facts
    theorems = system.theorems
    documents = system.documents if hasattr(system, "documents") else {}

    fact_names = list(facts.keys())
    theorem_names = list(theorems.keys())
    doc_names = list(documents.keys()) if isinstance(documents, dict) else []

    return json.dumps({
        "session_id": session_id,
        "documents": doc_names,
        "facts_count": len(facts),
        "theorems_count": len(theorems),
        "facts": fact_names[:20],
        "theorems": theorem_names[:20],
        "has_more": len(facts) > 20 or len(theorems) > 20,
    })


@mcp.tool()
def parseltongue_query(session_id: str, wff: str) -> str:
    """Query the system with a well-formed formula (WFF).

    Args:
        session_id: Session ID
        wff: Well-formed formula to evaluate

    Returns:
        JSON with query result
    """
    system = get_session(session_id)

    try:
        result = system.query(wff)
        return json.dumps({"status": "ok", "wff": wff, "result": str(result)})
    except Exception as e:
        return json.dumps({"status": "error", "wff": wff, "error": str(e)})


@mcp.tool()
def parseltongue_list_sessions() -> str:
    """List all active sessions.

    Returns:
        JSON with list of sessions
    """
    sessions = []
    for sid, system in _sessions.items():
        sessions.append({
            "session_id": sid,
            "facts_count": len(system.facts),
            "theorems_count": len(system.theorems),
        })
    return json.dumps({"sessions": sessions, "count": len(sessions)})


@mcp.tool()
def parseltongue_clear_session(session_id: str) -> str:
    """Clear all state from a session, keeping the session alive.

    Args:
        session_id: Session ID

    Returns:
        JSON with clear status
    """
    if session_id not in _sessions:
        return json.dumps({"status": "not_found", "session_id": session_id})

    _sessions[session_id] = System(overridable=True)
    return json.dumps({"status": "cleared", "session_id": session_id})


@mcp.tool()
def parseltongue_dsl_reference() -> str:
    """Get the Parseltongue DSL reference documentation.

    Returns:
        Full DSL reference as a string
    """
    from parseltongue import llm_doc
    return llm_doc()


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """CLI entry point - run the MCP server."""
    import logging
    # Suppress all logging to avoid polluting the JSON-RPC stream
    logging.disable(logging.CRITICAL)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
