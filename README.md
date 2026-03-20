# parseltongue-claude

MCP server wrapping [Parseltongue's](https://github.com/sci2sci-opensource/parseltongue) symbolic verification engine for Claude Code.

## Why?

Parseltongue catches LLM hallucinations by requiring every claim to trace back to a verbatim quote from source documents. The original architecture has Parseltongue call an LLM API. This inverts it: **Claude Code becomes the LLM, Parseltongue becomes a verification tool.**

```
Original:     You -> Parseltongue -> LLM API -> DSL -> Verify
This:         You -> Claude Code -> Parseltongue MCP -> Verify
```

No API key needed - uses your existing Claude Code subscription.

## Installation

```bash
# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

## Claude Code Setup

Add to `~/.claude.json` under `mcpServers` (user scope):

```json
{
  "mcpServers": {
    "parseltongue": {
      "type": "stdio",
      "command": "/path/to/parseltongue-claude/run-server.sh",
      "args": [],
      "env": {}
    }
  }
}
```

Or use the CLI:

```bash
claude mcp add --transport stdio parseltongue -- /path/to/parseltongue-claude/run-server.sh
```

Then restart Claude Code.

### Skill Installation (Optional)

The repo includes a Claude Code skill for guided document analysis:

```bash
# Symlink the skill to your skills directory
mkdir -p ~/.claude/skills
ln -s /path/to/parseltongue-claude/skills/parseltongue ~/.claude/skills/parseltongue
```

Then use `/parseltongue [document] [question]` in Claude Code.

## Usage

In Claude Code:

```
You: Analyze this SEC filing for red flags [paste document]

Claude Code:
  1. parseltongue_create_session("sec-review")
  2. parseltongue_register_document("sec-review", "10k", <content>)
  3. *generates DSL with facts citing verbatim quotes*
  4. parseltongue_load_dsl("sec-review", <dsl>)
  5. *checks unverified claims, iterates*
  6. Returns grounded analysis with citations
```

## Tools

| Tool | Description |
|------|-------------|
| `parseltongue_create_session` | Create a new verification session |
| `parseltongue_register_document` | Register source document for evidence grounding |
| `parseltongue_load_dsl` | Load DSL (facts, derives, diffs) and verify |
| `parseltongue_check_consistency` | Full consistency check |
| `parseltongue_get_state` | Get current session state |
| `parseltongue_query` | Query system with a WFF |
| `parseltongue_dsl_reference` | Get Parseltongue DSL docs |

## DSL Quick Reference

```parseltongue
# Extract a fact with verbatim evidence
fact revenue-q3
  :value 42000000
  :evidence
    :doc "10k"
    :quote "Total revenue for Q3 2024 was $42 million"

# Derive conclusions from facts
derive beat-target
  :using [revenue-q3, target-q3]
  :wff (> revenue-q3 target-q3)

# Cross-check with diffs
diff revenue-consistency
  :left revenue-q3
  :right revenue-breakdown-sum
  :expect (= left right)
```

See `parseltongue_dsl_reference` tool for full documentation.

## Development

```bash
uv pip install -e ".[dev]"                # install
pre-commit install --hook-type commit-msg --hook-type pre-commit  # hooks
pytest                                     # test (80% coverage required)
ruff check --fix . && ruff format .        # lint + format
ty check src/                              # type check
cz commit                                  # conventional commit
```

## License

Apache-2.0
