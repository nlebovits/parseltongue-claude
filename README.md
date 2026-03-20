# parseltongue-claude

MCP server + skill for [Parseltongue](https://github.com/sci2sci-opensource/parseltongue) hallucination detection in Claude Code.

## Quick Start

```bash
# 1. Install
uv pip install -e .

# 2. Add MCP server
claude mcp add --transport stdio parseltongue -- $(pwd)/run-server.sh

# 3. Install skills
mkdir -p ~/.claude/skills
ln -s $(pwd)/skills/parseltongue ~/.claude/skills/parseltongue
ln -s $(pwd)/skills/parseltongue-review ~/.claude/skills/parseltongue-review

# 4. Restart Claude Code, then:
/parseltongue [document] What are the key claims?
/parseltongue-review README.md  # audit your own docs
```

## What It Does

Inverts Parseltongue's architecture: instead of Parseltongue calling an LLM API, **Claude Code becomes the LLM** and calls Parseltongue for verification.

```
Original:     You → Parseltongue → LLM API → DSL → Verify
This:         You → Claude Code → Parseltongue MCP → Verify
```

Every claim must cite a verbatim quote. Misquotes are flagged as hallucinations.

## Skills

**`/parseltongue`** — Grounded document analysis

Analyze external documents with provable claims. Every fact traces to a verbatim quote.

```
/parseltongue [SEC filing] Are there revenue recognition red flags?
```

**`/parseltongue-review`** — Documentation audit

Audit docs for accuracy, duplication, and consistency with source.

```
/parseltongue-review README.md      # vs upstream, find duplicated content
/parseltongue-review docs/          # audit mkdocs site
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `parseltongue_create_session` | Create verification session |
| `parseltongue_register_document` | Register source document |
| `parseltongue_load_dsl` | Load DSL and verify quotes |
| `parseltongue_check_consistency` | Full consistency check |
| `parseltongue_dsl_reference` | Get DSL docs |

See [upstream Parseltongue docs](https://github.com/sci2sci-opensource/parseltongue) for DSL syntax and examples.

## Development

```bash
uv pip install -e ".[dev]"                              # install
uv run pre-commit install --hook-type commit-msg --hook-type pre-commit
uv run pytest                                           # test (80% coverage)
uv run ruff check --fix . && uv run ruff format .       # lint + format
uv run cz commit                                        # conventional commit
```

## License

Apache-2.0
