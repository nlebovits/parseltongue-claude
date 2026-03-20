# Parseltongue Claude - Project Instructions

MCP server wrapping Parseltongue's symbolic verification engine for Claude Code integration.

## Architecture

This project **inverts** the typical Parseltongue flow:
- Original: Parseltongue calls LLM API to generate DSL
- This: Claude Code generates DSL, calls Parseltongue to verify

The MCP server exposes Parseltongue's core engine as tools. Sessions are stored in memory.

## Key Files

```
src/parseltongue_claude/
├── __init__.py     # Package version
└── server.py       # MCP server with all tools
```

## Development

```bash
# Install
uv pip install -e ".[dev]"

# Test the server manually
python -m parseltongue_claude.server

# Run tests
pytest
```

## Adding New Tools

1. Add tool definition to `list_tools()` in server.py
2. Add case to `_handle_tool()` match statement
3. Implement handler function `_your_tool_name()`

## Parseltongue DSL

When generating DSL for verification:

1. **Facts** must have `:evidence` blocks with verbatim `:quote` from registered documents
2. **Derives** use `:wff` (well-formed formula) and `:using` to cite dependencies
3. **Diffs** cross-check values with `:expect` formulas

If a quote doesn't match the source document exactly, Parseltongue flags it as unverified (hallucination).

## Integration Testing

Test with the actual parseltongue library:

```python
from parseltongue.core import System, load_source

system = System(overridable=True)
system.register_document("test", "The revenue was $42 million.")

dsl = '''
fact revenue
  :value 42000000
  :evidence
    :doc "test"
    :quote "The revenue was $42 million."
'''
load_source(system, dsl)
print(list(system.facts()))
```
