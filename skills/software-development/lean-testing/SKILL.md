---
name: lean-testing
description: "Universal testing infrastructure: Lean methodology + Lean prover + Property-based testing. Risk-based prioritization, test charters, contract schemas, mutation testing, formal verification. 5-project synthesis."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Testing, QA, Lean, TestPyramid, PropertyBased, MutationTesting, Exploratory, FormalVerification, LeanProver]
    related_skills: [test-driven-development, requesting-code-review, systematic-debugging]
---

# Lean Testing — Universal Infrastructure v2

Three-layer testing stack combining Lean methodology (process), Property-based testing (generative), and Lean prover (formal verification). Derived from analysis of 5 projects: Vetka_dwg, MPT, PIVOBOT, geo-converter, FAMILY_TREE.

## Architecture

```
Layer 3: Lean Prover        — mathematical proof (100% guarantee)
                                Only for pure algorithms, risk ≥ 18
                                
Layer 2: Property-Based     — generative testing (99.9% coverage)
                                For pure functions + contract validation
                                Bridge between Lean model and real code
                                
Layer 1: Lean Methodology   — risk-based, waste-free (practical coverage)
                                For ALL code, risk matrix, CI gates
```

## Function Classification (A/B/C/D)

| Category | Criteria | Methods |
|---|---|---|
| **A: Pure algorithm** | No I/O, deterministic | Lean proof + Property-based |
| **B: Protocol/Contract** | External data format | Contract test (schema) + Fuzz |
| **C: Integration** | Multiple modules, mocked deps | Integration test + Risk matrix |
| **D: UI/Visual** | Rendering, interaction | Exploratory charter + Snapshot |

## Risk Score

```
Risk = (Impact × Probability) + (Complexity × Volatility / 2)
≥ 20: CRITICAL | 12-19: HIGH | 6-11: MEDIUM | < 6: LOW
```

## Spec-First Workflow

```
Phase 1: SPECIFY → classify (A/B/C/D) → Lean spec or schema → risk score
Phase 2: IMPLEMENT → code + property test + contract test → pytest/vitest + lake build
Phase 3: PROVE → Lean theorem → lake build → property test becomes regression guard
```

## Universal CI Pipeline

```
Push → [lint + typecheck]     ← static, <5s
     → [unit + property]      ← fast, <30s
     → [integration]          ← medium, <5min
     → [lake build]           ← Lean proofs (if proofs/ exists)
     → [e2e]                  ← slow, PR only
Nightly → [mutation] + [security scan]
```

## What Can Be Proven in Lean

| Property | Theorem Shape | Use Case |
|---|---|---|
| Roundtrip | `parse(serialize(x)) = x` | Parsers, codecs |
| Injectivity | `f(a) = f(b) → a = b` | Transforms, hashing |
| Monotonicity | `a ≥ b → rank(a) ≤ rank(b)` | Scoring, sorting |
| Conservation | `count(in) ≤ count(out)` | Pipeline, data flow |
| Invariant | `valid(x) → valid(f(x))` | Layer validity, tree structure |
| Idempotency | `f(f(x)) = f(x)` | Sort, dedup, normalize |

**Cannot be proven:** OpenCV, LLM inference, UI rendering, network I/O, third-party APIs.

## Testing Heuristics

### FEW HICCUPPS (exploratory)
Familiar, Exhaustive, What-if, Habitual, Interfacing, Complex, Corner cases, Unusual, Platform, Performance, Stateful

### Boundary Values
0, -1, 1, MIN_INT, MAX_INT, empty, null, whitespace, Unicode/emoji, date edges, concurrency

## Anti-Patterns

- ❌ Ice cream cone (many E2E, few unit)
- ❌ Coverage chasing (100% with useless tests)
- ❌ Lean proof for UI (non-deterministic)
- ❌ 50 manual cases for parser (use property test)
- ❌ Testing the mock (not real code)
- ❌ No flaky policy ("just re-run")
- ❌ Proof for unstable API (wait until stable)
- ❌ 135KB monolith without tests (split first)

## Project Analysis (5 Repositories)

| Project | Language | Domain | Lean Prover Targets | Property Targets | Current Gaps |
|---|---|---|---|---|---|
| Vetka_dwg | Python | CV + CAD | GPS roundtrip, coord transform, DXF invariant | LLM JSON, preprocess | Flat tests, coverage 78<80, accuracy=0 |
| MPT | Python+TS | Web API + LLM | Config roundtrip | API contract, Redis cache | Few tests, no Linux CI |
| PIVOBOT | JS | Telegram bot | Achievement monotonicity | D1 SQL, bot handler fuzz | Add property tests (Stryker already exists!) |
| geo-converter | Python | Geodesy | CRS transform, NTv2 interpolation | Grid parsing | 0 tests, 135KB monolith, no CI |
| FAMILY_TREE | JS+TS | Web app | Tree structure preservation | D1 SQL, SVG coords | No CI, no mutation |

## Implementation Roadmap

```
Stage 0: Audit          → classify all functions, risk matrix (1 day/project)
Stage 1: Methodology    → structure tests, CI gates, waste removal (1 week)
Stage 2: Property-based → Hypothesis/fast-check for A+B categories (1 week)
Stage 3: Contract       → JSON schemas, schema validation (3 days)
Stage 4: Lean prover    → proofs for critical pure algorithms (2-4 weeks)
Stage 5: Mutation audit → mutmut/Stryker monthly on critical modules (ongoing)
```

## References and Scripts

| File | Description |
|------|-------------|
| `references/universal-rules.md` | 5-project synthesis: classification, risk patterns, spec-first workflow, CI, PR checklist, anti-patterns |
| `references/lean-prover-templates.lean` | Lean 4 proof templates: roundtrip, injectivity, monotonicity, conservation, invariant, config, JSON contract + lakefile |
| `references/test-charter-templates.md` | 15 test charter templates by risk type + session report template |
| `references/ci-pipeline-templates.md` | GitHub Actions pipeline, coverage gate, flaky quarantine, test quality report, Docker Compose |
| `references/quick-reference.md` | Decision tree, coverage targets, naming, mock guide, test data strategies, pre-merge checklist |
| `references/vetka-dwg-case-study.md` | Real project analysis: risk matrix, property test candidates, priority order |
| `references/schemas/llm_point_response.json` | JSON schema: LLM point recognition contract |
| `references/schemas/llm_edge_response.json` | JSON schema: LLM edge recognition contract |
| `references/schemas/telegram_update.json` | JSON schema: Telegram Bot API update contract |
| `references/schemas/d1_query_result.json` | JSON schema: Cloudflare D1 query result contract |
| `scripts/property_test_templates.py` | Hypothesis templates: roundtrip, commutativity, idempotency, invariants, state machines, API contracts |
| `scripts/test_health.py` | Suite health checker: slow tests, duplicates, missing assertions, flaky detection, coverage gaps, A-F score |
| `scripts/risk_matrix.py` | Risk prioritization: impact × probability + complexity × volatility → HTML + JSON |