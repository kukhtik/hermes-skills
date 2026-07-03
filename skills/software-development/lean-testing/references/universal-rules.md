# Universal Testing Rules — 5-Project Synthesis

Rules derived from analysis of 5 repositories: Vetka_dwg, MPT, PIVOBOT, geo-converter, FAMILY_TREE.

## 1. Function Classification (A/B/C/D)

Every function falls into exactly one category. Classification determines testing strategy.

| Category | Criteria | Testing Methods | Examples |
|---|---|---|---|
| **A: Pure algorithm** | Input → output, no I/O, deterministic | Lean proof (if critical) + Property-based | GPS parse, coord transform, achievement calc, tree relations |
| **B: Protocol/Contract** | External data format, API shape | Contract test (schema) + Property-based (fuzz) | LLM JSON, Telegram API, D1 SQL, REST endpoints |
| **C: Integration** | Multiple modules, external deps (mocked) | Integration test + Risk matrix | Pipeline orchestrator, Ollama service, Cloudflare Worker |
| **D: UI/Visual** | Rendering, user interaction, non-deterministic | Exploratory charter + Snapshot | QML views, React components, SVG drag-and-drop |

### Classification Rules
- If function touches network, disk, or DB → not A (even if logic is pure inside)
- If function accepts arbitrary external input → B (even if internally pure)
- If function calls 2+ modules → C
- If function produces pixels or DOM → D
- A function can be tested at multiple levels, but primary category drives investment

## 2. Risk Score Formula

```
Risk = (Impact × Probability) + (Complexity × Volatility / 2)
```

| Score | Level | Required Testing |
|---|---|---|
| ≥ 20 | CRITICAL | Lean proof + Property + Contract + Integration + Exploratory |
| 12-19 | HIGH | Property + Contract + Integration |
| 6-11 | MEDIUM | Unit + Smoke |
| < 6 | LOW | Smoke only |

### Universal Risk Patterns

| Pattern | Impact | Prob | Cplx | Vol | Score | Level |
|---|---|---|---|---|---|---|
| External format parser | 4 | 4 | 3 | 3 | 18.5 | HIGH |
| LLM JSON contract | 4 | 4 | 3 | 4 | 22.0 | CRITICAL |
| Coordinate transform | 5 | 3 | 5 | 2 | 20.0 | CRITICAL |
| API endpoint (auth, data) | 4 | 3 | 2 | 4 | 16.0 | HIGH |
| UI rendering | 2 | 3 | 2 | 5 | 11.0 | MEDIUM |
| Cache | 2 | 2 | 2 | 1 | 5.0 | LOW |
| DB migration | 5 | 2 | 4 | 2 | 18.0 | HIGH |
| Bot handler | 3 | 3 | 3 | 3 | 13.5 | HIGH |
| Monolith function (>1000 lines) | 4 | 4 | 5 | 2 | 21.0 | CRITICAL |

## 3. The Three-Layer Testing Stack

```
Layer 3: Lean Prover        — mathematical proof (100% guarantee)
                                Only for category A, risk ≥ 18
                                Only for pure functions with formal model
                                
Layer 2: Property-Based     — generative testing (99.9% coverage)
                                For categories A and B
                                Bridge between Lean model and real code
                                
Layer 1: Lean Methodology   — risk-based, waste-free (practical coverage)
                                For ALL categories
                                Risk matrix, test charters, CI gates
```

### Investment Distribution

| Layer | Effort | Coverage | When to invest |
|---|---|---|---|
| Methodology | Low (hours) | Practical | Always — baseline |
| Property-based | Medium (days) | 99.9% | Categories A + B |
| Lean prover | High (weeks) | 100% | Category A, risk ≥ 18, stable algorithm |

## 4. Lean Prover Integration Pattern

Full verification of Python/JS is impossible (no translator). Therefore:

```
1. Write Lean model (reference implementation + specification)
2. Prove theorem in Lean (lake build verifies)
3. Write property-based test in Python/JS
4. Property test checks: real implementation matches Lean model on 10k+ inputs
5. If property test passes → implementation matches proven model (high confidence)
```

### What Can Be Modeled in Lean

| Property | Lean Theorem Shape | Applicable To |
|---|---|---|
| Roundtrip | `parse(serialize(x)) = x` | Parsers, serializers, codecs |
| Injectivity | `f(a) = f(b) → a = b` | Coordinate transforms, hashing |
| Monotonicity | `a ≥ b → rank(a) ≤ rank(b)` | Scoring, achievements, sorting |
| Conservation | `count(input) ≤ count(output)` | Pipeline, data transform |
| Invariant | `valid(x) → valid(f(x))` | Layer validity, tree structure |
| Idempotency | `f(f(x)) = f(x)` | Sort, dedup, normalize |

### What Cannot Be Modeled

- OpenCV/image processing (C code, no formal model)
- LLM inference (non-deterministic, black box)
- UI rendering (pixels, not logic)
- Network I/O (non-deterministic)
- Third-party APIs (external behavior)

## 5. Spec-First Development Workflow

### Before (code-first):
```
Idea → Code → Tests (maybe) → Deploy → Bugs → Fix
```

### After (spec-first):
```
Phase 1: SPECIFY (before code)
  → Classify function (A/B/C/D)
  → If A: write Lean specification
  → If B: write JSON schema / type contract
  → Calculate risk score
  → Decide: which test methods, how many

Phase 2: IMPLEMENT (code + tests together)
  → Write implementation
  → Write property test (checks against Lean model)
  → Write contract test (if B)
  → Run: pytest/vitest + lake build

Phase 3: PROVE (when model stabilizes)
  → Prove theorem in Lean
  → lake build verifies proof
  → Property test becomes regression guard (proof is stronger)
```

## 6. Universal CI Pipeline

```yaml
# .github/workflows/ci.yml — universal template
name: CI

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * *'  # Nightly

jobs:
  static:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: lint              # ruff / eslint
      - run: typecheck         # mypy / tsc

  unit-property:
    runs-on: ubuntu-latest
    needs: static
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/unit/ tests/property/ -v  # or vitest
      - run: pytest --cov --cov-fail-under=80

  integration:
    runs-on: ubuntu-latest
    needs: unit-property
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration/ -v

  e2e:
    runs-on: ubuntu-latest
    needs: integration
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/e2e/ -v --maxfail=1

  proofs:
    runs-on: ubuntu-latest
    needs: static
    if: hashFiles('proofs/lakefile.lean') != ''
    steps:
      - uses: actions/checkout@v4
      - run: |
          curl -fsSL https://lean-lang.org/install/lean.sh | bash
          cd proofs && lake build

  nightly:
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 2 * * *'
    steps:
      - uses: actions/checkout@v4
      - run: mutmut run  # or stryker run
      - run: safety check  # or npm audit
```

## 7. Project Structure (Universal)

```
project/
├── src/                          # implementation
├── proofs/                       # Lean 4 models + proofs (optional)
│   ├── lakefile.lean
│   ├── Spec/                     # specifications (what we prove)
│   │   ├── Parser.lean
│   │   ├── Transform.lean
│   │   └── Invariants.lean
│   └── Proofs/                   # proofs (why it's true)
│       ├── Parser.lean
│       └── Transform.lean
├── tests/
│   ├── unit/                     # category C
│   ├── property/                 # category A + B
│   ├── e2e/                      # category D + real integration
│   ├── fixtures/
│   └── risk_matrix.yaml          # project risk matrix
├── schemas/                      # contract definitions (category B)
│   ├── llm_response.json
│   └── api_openapi.yaml
├── .github/workflows/
│   ├── ci.yml                    # unit + property (fast)
│   ├── nightly.yml               # mutation + security
│   └── proofs.yml                # lake build (Lean proofs)
└── pyproject.toml / package.json
```

## 8. PR Checklist (Universal)

```markdown
- [ ] Function category determined (A/B/C/D)
- [ ] If A — Lean specification in proofs/Spec/
- [ ] If B — JSON schema or type contract in schemas/
- [ ] Property test matches Lean model (if A)
- [ ] Risk score recalculated if complexity changed
- [ ] No category D tests for category A functions
- [ ] No category A proof for category D functions
- [ ] Mutation score not degraded (nightly check)
- [ ] lake build passes (if proofs/ exists)
- [ ] CI: unit + property < 30s
- [ ] CI: integration < 5min
```

## 9. Waste Elimination Rules (Universal)

| Don't write | Why | Instead |
|---|---|---|
| E2E test for pure function | Wrong layer | Property test |
| 50 manual cases for parser | Manual edge case hunt | 1 property test |
| Test that checks mock logic | Tests mock, not code | Test on real object |
| 100% coverage on getters | `return self._x` | Risk-gate |
| Test for unchanged 2yr code | Stable, low risk | Smoke test |
| Lean proof for UI | UI non-deterministic | Exploratory charter |
| Proof for unstable API | Spec keeps changing | Wait until stable |
| Unit test with real network | Non-deterministic | Mock + integration test |

## 10. Anti-Patterns (5-Project Derived)

| Anti-pattern | Found in | Fix |
|---|---|---|
| Flat test directory (no levels) | Vetka_dwg | Split: unit/property/integration/e2e |
| Coverage gate > actual coverage | Vetka_dwg (78 vs 80) | Fix coverage or lower gate |
| Accuracy metrics = 0.0 | Vetka_dwg | Add ground truth comparison |
| 135KB monolith file | geo-converter | Split into modules |
| No CI | geo-converter, FAMILY_TREE | Add GitHub Actions |
| No tests at all | geo-converter | Start with property-based for core algo |
| Stryker config but no mutation CI | PIVOBOT | Add nightly mutation job |
| Mutation already in use | PIVOBOT | Extend to all critical modules |