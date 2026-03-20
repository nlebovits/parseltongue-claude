---
name: parseltongue-review
description: Adversarial documentation audit using Parseltongue. Use when reviewing your own docs (README, mkdocs, API docs) for accuracy, duplication with upstream, and internal consistency. Invoke with "/parseltongue-review [file or topic]".
---

# Adversarial Doc Review

Audit your documentation for accuracy using Parseltongue verification.

## When to Use

- Reviewing README before release
- Auditing mkdocs site for accuracy
- Checking if docs duplicate upstream content
- Verifying API docs match implementation

## Instructions

### 1. Load Your Doc + Source of Truth

```
mcp__parseltongue__parseltongue_create_session
  session_id: "doc-review-{timestamp}"

mcp__parseltongue__parseltongue_register_document
  session_id: "doc-review-..."
  name: "my-doc"
  content: [your README/docs]

mcp__parseltongue__parseltongue_register_document
  session_id: "doc-review-..."
  name: "upstream"
  content: [upstream docs, source code, or authoritative source]
```

### 2. Extract Claims from Your Doc

For each claim in your documentation, create a fact:

```scheme
(fact claim-api-returns-json true
    :evidence (evidence "my-doc"
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
    :evidence (evidence "my-doc"
        :quotes ("Install with pip install foo")
        :explanation "This exact text appears in upstream"))
```

### 5. Run Consistency Check

```
mcp__parseltongue__parseltongue_check_consistency
  session_id: "doc-review-..."
```

Report:
- **Unverified claims** - Docs say something source doesn't support
- **Duplicated content** - Should link to upstream instead
- **Inconsistencies** - Conflicts between your docs and source

## Example

```
User: /parseltongue-review README.md

Claude: Loading README and fetching upstream docs...
        [registers both documents]

        Extracting claims from README...
        - "DSL syntax: fact, derive, diff" [ref:dsl-claim]
        - "80% test coverage required" [ref:coverage-claim]

        Cross-checking against upstream...
        ✗ DSL syntax duplicates upstream README
        ✓ Coverage requirement verified in pyproject.toml

        ## Findings

        **Remove (duplicates upstream):**
        - DSL Quick Reference section [ref:dsl-claim]

        **Keep (unique to this project):**
        - Coverage requirement [ref:coverage-claim]
        - Skill installation instructions
```

## Checklist

- [ ] Does every claim trace to source?
- [ ] Is duplicated content linked instead of copied?
- [ ] Are version numbers current?
- [ ] Do examples actually work?
