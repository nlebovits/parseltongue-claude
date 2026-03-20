---
name: parseltongue-review
description: Documentation audit using Parseltongue. Verify docs for accuracy, find duplicated content, check consistency with source. Invoke with "/parseltongue-review [file or directory]".
---

# Documentation Audit

Verify documentation accuracy using Parseltongue.

## When to Use

- Audit README for accuracy
- Review mkdocs site against source
- Find duplicated content that should link upstream
- Verify API docs match implementation
- Check consistency across doc pages

## Instructions

### 1. Load Docs + Source of Truth

```
mcp__parseltongue__parseltongue_create_session
  session_id: "doc-review-{timestamp}"

mcp__parseltongue__parseltongue_register_document
  session_id: "doc-review-..."
  name: "docs"
  content: [documentation to audit]

mcp__parseltongue__parseltongue_register_document
  session_id: "doc-review-..."
  name: "upstream"
  content: [upstream docs, source code, or authoritative source]
```

### 2. Extract Claims

For each claim in the documentation, create a fact:

```scheme
(fact claim-api-returns-json true
    :evidence (evidence "docs"
        :quotes ("Returns JSON response")
        :explanation "API behavior claim"))
```

### 3. Cross-Check Against Source

Use `diff` to verify claims match the source of truth:

```scheme
(diff api-behavior-matches
    :left claim-api-returns-json
    :right upstream-api-spec
    :expect (= left right))
```

### 4. Check for Duplication

If content appears in both docs verbatim, flag it:

```scheme
(fact duplicated-content true
    :evidence (evidence "docs"
        :quotes ("Install with pip install foo")
        :explanation "This exact text appears in upstream"))
```

### 5. Run Consistency Check

```
mcp__parseltongue__parseltongue_check_consistency
  session_id: "doc-review-..."
```

Report:
- **Unverified claims** — Docs say something source doesn't support
- **Duplicated content** — Should link to upstream instead
- **Inconsistencies** — Conflicts between docs and source

## Example

```
User: /parseltongue-review docs/

Claude: Loading docs and source files...
        [registers docs + source code/upstream]

        Extracting claims...
        - "API returns JSON" [ref:api-claim]
        - "Requires Python 3.11+" [ref:python-claim]
        - "Install with pip install foo" [ref:install-claim]

        Cross-checking...
        ✓ API returns JSON - verified in source
        ✓ Python 3.11+ - matches pyproject.toml
        ✗ Install instructions duplicate upstream

        ## Findings

        **Duplicated (link instead):**
        - Installation section [ref:install-claim]

        **Verified:**
        - API behavior [ref:api-claim]
        - Python version [ref:python-claim]
```

## Checklist

- [ ] Does every claim trace to source?
- [ ] Is duplicated content linked instead of copied?
- [ ] Are version numbers current?
- [ ] Do examples actually work?
