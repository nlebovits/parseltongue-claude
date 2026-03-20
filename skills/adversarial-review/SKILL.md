---
name: adversarial-review
description: Exhaustive adversarial documentation verification. Use when checking README accuracy, API documentation completeness, or any docs where missing features could mislead users. Enumerates ALL features from source, compares to docs, proves coverage gaps with formal logic.
---

# Adversarial Documentation Review

Catch what manual review misses: undocumented features, unverified claims, misleading examples.

## When to Use This Skill

- **README/docs review:** "Is this README accurate and complete?"
- **API documentation audit:** "Are all methods documented?"
- **Performance claims:** "Are these benchmarks real?"
- **Migration guides:** "Does this show all breaking changes?"

**Red flags that trigger adversarial review:**
- Quantitative claims without evidence ("5x faster")
- Selective examples (shows 1 of 8 subcommands)
- Version-dependent claims (could be outdated)

## The Adversarial Difference

| Manual Review | Adversarial Review |
|---------------|-------------------|
| "Looks comprehensive" | **82.5% coverage (33/40 methods)** |
| "Examples seem right" | **7 methods undocumented** (proven via derivation) |
| "5x claim noted" | **Unverified** (no benchmark files found) |
| Miss check method gap | **Formal proof** 4 variants missing |

## Instructions

### Phase 1: Exhaustive Enumeration (Ground Truth)

**Build complete inventories from source code, not docs.**

#### For CLI Tools:

```bash
# Extract ALL commands and subcommands
uv run tool --help | grep "Commands:" -A 100
uv run tool add --help | awk '/Commands:/,/^$/' 
uv run tool check --help | awk '/Commands:/,/^$/'

# Count total
echo "add subcommands: 8 total"
echo "check subcommands: 7 total"
```

#### For Python APIs:

```python
# Extract all public methods from source
import ast

with open('api/table.py') as f:
    tree = ast.parse(f.read())

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'Table':
        methods = [m.name for m in node.body 
                  if isinstance(m, ast.FunctionDef) 
                  and not m.name.startswith('_')]
        print(f"Total public methods: {len(methods)}")
        for m in sorted(methods):
            print(f"  {m}")
```

**Critical:** This is your **ground truth**. Docs must be measured against THIS, not assumed complete.

### Phase 2: Document What's Documented

**Extract claims from README/docs.**

```bash
# For READMEs
grep "gpio add" README.md  # Shows which commands are mentioned
grep "\.add_" README.md    # Shows which methods are shown

# For API docs
grep "^####" docs/api/python-api.md | sed 's/#### //' | awk -F'(' '{print $1}'
```

**Build inventory:**
- Which commands are shown in examples?
- Which parameters are documented?
- What's mentioned in prose vs shown in code?

### Phase 3: Create Parseltongue Verification

**Register evidence documents:**

```python
mcp__parseltongue__parseltongue_create_session(
    session_id="adversarial-review"
)

mcp__parseltongue__parseltongue_register_document(
    session_id="adversarial-review",
    name="ground_truth",
    content="""
ACTUAL CLI COMMANDS (from --help):
add subcommands: a5, admin-divisions, bbox, bbox-metadata, h3, kdtree, quadkey, s2
Total: 8 subcommands

ACTUAL Table CLASS METHODS (from source):
add_bbox, add_h3, check, check_bbox, check_compression, check_spatial, ...
Total: 40 public methods
"""
)

mcp__parseltongue__parseltongue_register_document(
    session_id="adversarial-review",
    name="documentation",
    content="""
README SHOWS (from grep):
- gpio add bbox
Total add subcommands shown: 1

PYTHON API DOCS SHOW:
add_bbox, add_h3, check, validate, ...
Total methods documented: 33
"""
)
```

### Phase 4: Build Adversarial DSL

**Pattern 1: Coverage Analysis**

```scheme
(defterm total-actual-commands 8
  :evidence (evidence "ground_truth"
    :quotes ("Total: 8 subcommands")
    :explanation "Count from CLI --help"))

(defterm readme-shows-commands 1
  :evidence (evidence "documentation"
    :quotes ("gpio add bbox")
    :explanation "Only bbox shown"))

(defterm coverage-ratio (/ readme-shows-commands total-actual-commands)
  :origin "calculated")

(derive poor-coverage (< coverage-ratio 0.2)
  :using (coverage-ratio))
```

**Pattern 2: Specific Feature Gaps**

```scheme
(fact cli-has-extract-bigquery true
  :evidence (evidence "ground_truth"
    :quotes ("extract subcommands: arcgis, bigquery, geoparquet")
    :explanation "bigquery exists in CLI"))

(fact readme-shows-extract-bigquery false
  :origin "manual verification - not in README")

(derive undocumented-feature
  (and cli-has-extract-bigquery (not readme-shows-extract-bigquery))
  :using (cli-has-extract-bigquery readme-shows-extract-bigquery))

(diff missing-bigquery-docs
  :replace readme-shows-extract-bigquery
  :with true)
```

**Pattern 3: Performance Claims Need Evidence**

```scheme
(fact performance-claim-made true
  :evidence (evidence "documentation"
    :quotes ("5x better performance")
    :explanation "Quantitative claim"))

(fact benchmark-files-exist false
  :evidence (evidence "filesystem"
    :quotes ("ls benchmarks/ → directory not found")
    :explanation "No benchmark evidence"))

(derive unverified-claim
  (and performance-claim-made (not benchmark-files-exist))
  :using (performance-claim-made benchmark-files-exist))
```

**Pattern 4: Method Signature Drift**

```scheme
(fact readme-example-signature
  "partition_by_h3('output/', resolution=5)"
  :evidence (evidence "documentation"
    :quotes ("partition_by_h3('output/', resolution=5)")
    :explanation "Example from README"))

(fact actual-signature
  "def partition_by_h3(self, output_dir, *, resolution=9, ...)"
  :evidence (evidence "ground_truth"
    :quotes ("partition_by_h3(output_dir, *, resolution: int = 9")
    :explanation "From source code"))

(derive signature-matches
  (= readme-example-signature actual-signature)
  :using (readme-example-signature actual-signature))
```

### Phase 5: Run Consistency Check

```python
result = mcp__parseltongue__parseltongue_check_consistency(
    session_id="adversarial-review"
)

# Look for:
# - Unverified facts (quotes didn't match)
# - Failed diffs (expected vs actual mismatch)
# - Fabrication taint (unverified evidence propagated)
```

### Phase 6: Generate Adversarial Report

**Template:**

```markdown
## Adversarial Documentation Review

### Coverage Analysis

**Theorem:** `poor-coverage` ✓ proven (12.5% coverage)

- **Total features:** 8
- **Documented:** 1
- **Coverage ratio:** 12.5% (Grade: F)

**Parseltongue proof:**
(defterm coverage-ratio (/ 1 8))  ; = 0.125
(derive poor-coverage (< 0.125 0.2))

### Undocumented Features

**Theorem:** `undocumented-feature` ✓ proven

The following features exist in code but are NOT mentioned in docs:

1. `extract bigquery` - Extract from BigQuery tables
2. `add a5` - Add A5 spatial index
3. `check spec` - Validate GeoParquet spec compliance
[...7 more]

**Evidence chain:**
(fact cli-has-extract-bigquery true :evidence ...)
(fact readme-shows-extract-bigquery false)
(derive undocumented-feature ...)

### Unverified Claims

**Theorem:** `unverified-claim` ✓ proven

**Claim:** "5x better performance than CLI operations"
**Evidence:** No benchmark files found
**Status:** 🔴 UNVERIFIED

### Recommendations

1. **Immediate:** Document all 8 add subcommands (currently 87.5% missing)
2. **High:** Add benchmark data or remove "5x" claim
3. **Medium:** Create exhaustive API reference (not just examples)
```

## Key Adversarial Patterns

### Completeness Axioms

```scheme
; AXIOM: All CLI commands must be documented
(axiom all-commands-documented
  (implies (exists-in-cli ?cmd) (exists-in-docs ?cmd))
  :origin "documentation standard")

; DERIVE violations
(derive undocumented-commands
  (set-difference cli-commands doc-commands)
  :using (cli-commands doc-commands))
```

### Quantitative Claims Require Evidence

```scheme
; AXIOM: Performance claims need benchmarks
(axiom performance-needs-proof
  (implies (is-performance-claim ?claim) (exists-benchmark ?claim))
  :origin "adversarial review standard")

(fact fivex-claim
  "5x better performance"
  :evidence (evidence "README" :quotes (...)))

(fact has-benchmarks false
  :evidence (evidence "filesystem" :quotes ("no benchmark files")))

; This derive FAILS if no benchmarks
(derive claim-verified
  (exists-benchmark fivex-claim)
  :using (has-benchmarks))
```

### Negative Verification (What's NOT True)

```scheme
; Check for claims about features that don't work
(fact readme-claims-azure-support true
  :evidence (evidence "README"
    :quotes ("Read from and write to S3, GCS, Azure")
    :explanation "Azure claimed"))

(fact azure-tests-exist false
  :evidence (evidence "tests"
    :quotes ("grep -r 'azure://' tests/ → 0 matches")
    :explanation "No Azure tests"))

(derive untested-claim
  (and readme-claims-azure-support (not azure-tests-exist))
  :using (readme-claims-azure-support azure-tests-exist))
```

## Adversarial Checklist

Before claiming docs are "accurate":

- [ ] **Exhaustive enumeration:** Built ground truth from source
- [ ] **Coverage calculation:** Computed exact % documented
- [ ] **Gap analysis:** Identified specific missing features
- [ ] **Claim verification:** Checked all quantitative claims have evidence
- [ ] **Negative checks:** Looked for claims about non-existent features
- [ ] **Signature validation:** Verified examples match actual APIs
- [ ] **Version coherence:** Checked for deprecated examples
- [ ] **Formal proofs:** Used Parseltongue derivations, not assumptions

## Output Format

**Always include:**

1. **Theorems proven** with formal derivations
2. **Coverage metrics** with exact percentages
3. **Specific gaps** (not "some methods missing")
4. **Evidence chains** showing provenance
5. **Grade** (A-F based on coverage and accuracy)

**Example:**

```
## Verification Results

✅ Theorems Proven: 7
🔴 Critical Gaps: 4
📊 Coverage: 82.5% (33/40 methods)
⚠️ Unverified Claims: 1

Grade: B+ (docs mostly complete with minor gaps)
```

## Anti-Patterns to Avoid

❌ **"Looks comprehensive"** → Calculate exact coverage
❌ **"Examples are correct"** → Check ALL features, not just examples
❌ **"Performance seems better"** → Require benchmark evidence
❌ **Assuming completeness** → Enumerate from source, not docs
❌ **Surface-level checking** → Use formal derivations

## Why This Works

**Parseltongue enforces:**
- Every claim traces to source quote (no guessing)
- Derivations are formal logic (no hand-waving)
- Fabrications propagate (one bad quote taints conclusions)
- Diffs expose mismatches (expected vs actual)

**Result:** Documentation gaps become **provable theorems**, not subjective assessments.
