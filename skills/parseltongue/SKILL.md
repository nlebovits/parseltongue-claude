---
name: parseltongue
description: Grounded document analysis with hallucination detection. Use when analyzing documents, reports, papers, or any text where claims must be verifiable. Extracts facts with verbatim quotes, derives conclusions, and catches fabricated claims. Invoke with "/parseltongue [document or query]".
---

# Parseltongue Grounded Analysis

Analyze documents with provable claims. Every fact traces to a verbatim quote. Hallucinations are automatically detected.

## Quick Start

```
/parseltongue [paste document] What are the key findings?
```

Or with a file:
```
/parseltongue @report.pdf Are there any red flags in this SEC filing?
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. REGISTER    │  Load document into Parseltongue session          │
│  2. EXTRACT     │  Generate facts with verbatim :evidence quotes    │
│  3. DERIVE      │  Draw conclusions using formal logic              │
│  4. VERIFY      │  Check all quotes match source (catch hallucinations) │
│  5. ANSWER      │  Respond with [ref:symbol] citations              │
└─────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Create Session & Register Document

```
mcp__parseltongue__parseltongue_create_session
  session_id: "analysis-{timestamp}"

mcp__parseltongue__parseltongue_register_document
  session_id: "analysis-..."
  name: "doc"  # or descriptive name like "10k-filing"
  content: [document text]
```

### Step 2: Extract Facts (Pass 1)

Generate Parseltongue DSL with facts. **Every fact MUST have a verbatim quote.**

```scheme
(fact revenue-q3 42000000
    :evidence (evidence "doc"
        :quotes ("Total revenue for Q3 2024 was $42 million")
        :explanation "Quarterly revenue figure"))

(fact growth-target 40000000
    :evidence (evidence "doc"
        :quotes ("Growth target was $40 million")
        :explanation "Target figure for comparison"))
```

**Rules:**
- `:quotes` must be EXACT text from the document (case-insensitive matching allowed)
- One fact per distinct claim
- Use descriptive symbol names (kebab-case)

Load and check:
```
mcp__parseltongue__parseltongue_load_dsl
  session_id: "analysis-..."
  dsl_source: [your DSL]
```

If `unverified_count > 0`, you hallucinated! Fix the quotes.

### Step 3: Derive Conclusions (Pass 2)

Draw logical conclusions from verified facts:

```scheme
(derive beat-target
    :using [revenue-q3 growth-target]
    :wff (> revenue-q3 growth-target))

(derive growth-percentage
    :using [revenue-q3 growth-target]
    :wff (* (/ (- revenue-q3 growth-target) growth-target) 100))
```

Load and verify these too.

### Step 4: Cross-Check with Diffs (Pass 3)

Add consistency checks where values should match:

```scheme
(diff revenue-consistency
    :left revenue-q3
    :right (+ revenue-north revenue-south revenue-west)
    :expect (= left right))
```

### Step 5: Get Reference & Answer

```
mcp__parseltongue__parseltongue_dsl_reference
```

Returns full DSL documentation if you need syntax help.

```
mcp__parseltongue__parseltongue_check_consistency
  session_id: "analysis-..."
```

Returns full verification report.

### Step 6: Respond with Citations

Format your answer with `[ref:symbol]` citations:

```markdown
The company beat its growth target [ref:beat-target], achieving
$42M in revenue [ref:revenue-q3] against a $40M target
[ref:growth-target]. This represents a 5% overperformance
[ref:growth-percentage].
```

## DSL Quick Reference

| Directive | Purpose | Key Fields |
|-----------|---------|------------|
| `fact` | Ground truth with evidence | `:evidence (evidence "doc" :quotes (...))` |
| `axiom` | Rewrite rule | `:origin "source"`, must have `?var` |
| `defterm` | Named term/alias | `:origin "definition"` |
| `derive` | Logical conclusion | `:using [symbols]`, `:wff (formula)` |
| `diff` | Cross-check | `:left`, `:right`, `:expect` |

## Common Formulas

```scheme
; Comparison
(> a b)  (< a b)  (= a b)  (>= a b)  (<= a b)

; Arithmetic
(+ a b)  (- a b)  (* a b)  (/ a b)

; Logic
(and p q)  (or p q)  (not p)  (if p q)  (iff p q)

; Quantifiers (with ?vars)
(forall ?x (P ?x))  (exists ?x (P ?x))
```

## Handling Hallucinations

When `unverified_count > 0`:

1. **Check the quotes** - Are they exact? Whitespace matters less, but words must match.
2. **Check the document name** - Does it match what you registered?
3. **Simplify** - Use shorter, more distinctive quotes.
4. **Re-extract** - If you can't find a quote, the claim may be fabricated.

**This is the point.** The system catches when you make claims that aren't in the source.

## Example Session

```
User: /parseltongue [SEC 10-K excerpt] Any concerns about revenue recognition?

Claude: Creating session and registering document...
        [calls mcp__parseltongue__parseltongue_create_session]
        [calls mcp__parseltongue__parseltongue_register_document]

        Extracting facts from filing...
        [generates DSL with revenue-related facts]
        [calls mcp__parseltongue__parseltongue_load_dsl]

        ✓ 12 facts verified
        ✗ 1 fact unverified: "revenue-timing" - quote not found

        Fixing hallucinated claim...
        [regenerates with correct quote]

        ✓ All 13 facts verified

        Deriving conclusions...
        [adds derive directives]

        Running consistency check...
        [calls mcp__parseltongue__parseltongue_check_consistency]

        ## Analysis

        Revenue recognition appears aggressive [ref:accrual-timing].
        The company recognized $15M [ref:q4-revenue] in Q4 despite
        delivery occurring in January [ref:delivery-date], which
        violates ASC 606 timing requirements [ref:asc606-violation].

        ### Verified Claims
        - Q4 revenue: $15M [ref:q4-revenue]
        - Delivery date: January 15 [ref:delivery-date]
        - Recognition date: December 28 [ref:recognition-date]

        ### Consistency Issues
        - [diff:timing-check] FAILED: recognition before delivery
```

## When to Use This Skill

- **SEC filings** - Verify financial claims
- **Research papers** - Check methodology and results
- **Legal documents** - Trace claims to specific clauses
- **News articles** - Verify quotes and attributions
- **Technical docs** - Validate specs against implementation

## When NOT to Use

- Creative writing (no source to verify against)
- Opinion pieces (claims are inherently subjective)
- Real-time data (document is the snapshot)
