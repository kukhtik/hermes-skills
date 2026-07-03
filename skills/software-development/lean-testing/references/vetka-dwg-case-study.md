# Case Study: Vetka_dwg — Testing Plan for Photo→DWG Pipeline

Real project analysis (2026-07-03). Repo: `kukhtik/Vetka_dwg` (private, Python, PySide6/QML + OpenCV + Qwen2VL LLM + ezdxf).

## Project Profile

- **Purpose:** GUI app — photo of survey abris + GPS file + DXF template → auto-generated DXF drawing
- **Stack:** Python 3.11, PySide6/QML, OpenCV, Qwen2VL (LLM vision), ezdxf
- **Architecture:** 4 layers — UI (QML) → Bridges (Qt↔Python) → Pipeline orchestrator → IO/Vision/Mapping/DXF
- **Size:** 86 Python files, 15 QML files, 38 test files, 98MB (includes fixtures)
- **CI:** GitHub Actions (Windows), pytest + ruff + mypy, coverage gate 80%

## Existing Testing State

### Already Good ✅
- 4-level test strategy documented (unit/integration/e2e/GUI)
- MockLLMPlugin for testing pipeline without real LLM
- Real fixtures: photos, GPS files, DXF templates
- Baseline metrics file (`tests/baseline.yaml`)
- E2E test with mock LLM (`test_vekker_meets_metrics.py`)
- Accuracy comparison script (`scripts/accuracy_metrics.py`)
- CI pipeline with lint + type check + coverage

### Gaps Identified ❌
1. Tests flat in `tests/` — not split into unit/integration/e2e directories
2. Coverage at 78%, gate at 80% — CI may fail
3. Accuracy metrics all 0.0 — no ground truth baseline established
4. No property-based tests (parsers are ideal candidates)
5. No mutation testing (coverage quality unknown)
6. No GUI snapshot tests (TestShell.qml exists but no tests/gui/)
7. CI only on Windows — no Linux/macOS matrix
8. No flaky detection for E2E tests with real photos
9. No contract/schema validation for LLM JSON responses

## Risk Matrix (Impact × Probability + Complexity × Volatility / 2)

| Component | Imp | Prob | Cplx | Vol | Score | Level | Strategy |
|---|---|---|---|---|---|---|---|
| LLM JSON parsing | 4 | 4 | 3 | 4 | 22.0 | CRITICAL | Contract + Property + Fuzz |
| Semantic mapping | 4 | 4 | 4 | 3 | 22.0 | CRITICAL | Integration + E2E |
| DXF builder | 5 | 3 | 4 | 2 | 19.0 | HIGH | Unit + Integration |
| Pipeline orchestrator | 5 | 2 | 3 | 3 | 14.5 | HIGH | Integration + E2E |
| Preprocess (OpenCV) | 3 | 3 | 5 | 2 | 14.0 | HIGH | Unit + Property (images) |
| GPS parser | 4 | 3 | 2 | 3 | 13.0 | HIGH | Unit + Property |
| Template parser | 4 | 2 | 4 | 2 | 12.0 | HIGH | Unit + Property |
| QML UI | 2 | 3 | 2 | 5 | 11.0 | MEDIUM | GUI snapshot |
| Cache (template) | 2 | 2 | 2 | 1 | 5.0 | LOW | Smoke |

## Recommended Test Structure

```
tests/
├── unit/                    # Fast, isolated, MockLLM
│   ├── io/                  # gps, photo, template, cache
│   ├── vision/             # preprocess, regions, prompts
│   ├── mapping/            # classify, matcher, semantic
│   ├── scene/              # types, build
│   └── dxf/                # builder, writer, report
├── integration/            # Modules together, MockLLM
│   ├── test_pipeline.py
│   ├── test_bridge.py
│   └── test_mapping_with_template.py
├── e2e/                     # Real LLM, real fixtures
│   └── test_vekker_meets_metrics.py
├── gui/                     # pytest-qt, snapshot
│   ├── test_review_view.py
│   └── test_template_library.py
├── property/               # Hypothesis, all inputs
│   ├── test_gps_property.py
│   ├── test_dxf_roundtrip.py
│   └── test_llm_json_contract.py
└── conftest.py
```

## Key Property-Based Test Candidates

### GPS Parser (roundtrip)
```python
@given(st.lists(
    st.tuples(st.integers(min_value=1), st.floats(-90, 90), st.floats(-180, 180)),
    min_size=1, max_size=100
))
def test_gps_parse_roundtrip(points):
    text = "\n".join(f"{n} {lat} {lon}" for n, lat, lon in points)
    parsed = parse_gps(text)
    assert len(parsed) == len(points)
```

### DXF Writer/Reader (roundtrip)
```python
@given(st.lists(
    st.tuples(st.floats(-1e6, 1e6, allow_nan=False),
              st.floats(-1e6, 1e6, allow_nan=False)),
    min_size=0, max_size=50
))
def test_dxf_points_roundtrip(coords):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for x, y in coords:
        msp.add_point((x, y))
    # write → read → compare
```

### LLM JSON Contract (never crash)
```python
@given(st.dictionaries(
    keys=st.sampled_from(["number", "bbox", "confidence", "text"]),
    values=st.one_of(st.integers(), st.floats(0, 1), st.text(max_size=50)),
))
def test_parse_llm_json_never_crashes(data):
    json_str = json.dumps(data)
    result = parse_llm_json(json_str)
    assert result is not None or data == {}
```

## CI Fix: Matrix + Proper Test Separation

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev,ui]"
      - run: pytest tests/unit/ tests/property/ -v --tb=short -q
      - run: pytest tests/integration/ -v --tb=short -q
      - run: ruff check vetka_dwg/ tests/
      - run: mypy vetka_dwg/ --strict --no-error-summary
      - run: pytest tests/ --cov=vetka_dwg --cov-report=term-missing --cov-fail-under=80 --ignore=tests/e2e/
```

## Priority Order

1. Property-based for GPS parser (1h) → all edge cases
2. Contract tests for LLM JSON (30min) → malformed responses
3. Fix coverage 78→80% (1h) → CI green
4. Structure tests by level (2h) → match strategy
5. Fill accuracy baseline (2h) → real metrics
6. Mutation audit (1h) → test quality check
7. GUI snapshot tests (3h) → UI regression
8. CI matrix Linux+Windows (30min) → cross-platform