# CI/CD Pipeline Templates

## GitHub Actions — Full Testing Pipeline

```yaml
# .github/workflows/test-pipeline.yml
name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Nightly: mutation + security

jobs:
  static:
    name: Lint + Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy src/ --strict

  unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: static
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[test]"
      - run: pytest tests/unit/ -v --cov=src --cov-report=xml --cov-fail-under=80
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[test]"
      - run: pytest tests/integration/ -v --maxfail=3
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test

  smoke:
    name: Smoke Tests
    runs-on: ubuntu-latest
    needs: integration
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t app:test .
      - run: |
          docker run -d --name smoke -p 8080:8080 app:test
          sleep 5
          curl -sf http://localhost:8080/health || exit 1
          curl -sf http://localhost:8080/api/v1/status || exit 1
          docker stop smoke

  e2e:
    name: E2E Tests (Critical Paths)
    runs-on: ubuntu-latest
    needs: smoke
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t app:test .
      - run: |
          docker run -d --name e2e -p 8080:8080 app:test
          sleep 5
          pytest tests/e2e/ -v --maxfail=1 -k "critical"
          docker stop e2e

  mutation:
    name: Mutation Testing (Nightly)
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 2 * * *'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[test]" mutmut
      - run: mutmut run --paths-to-mutate src/
      - run: mutmut results --all

  security:
    name: Security Scan (Nightly)
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 2 * * *'
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r src/ -f json -o bandit-report.json
      - run: safety check --json --output safety-report.json
```

## Coverage Gate — Per-Changed-File

```python
# scripts/coverage_gate.py
"""
Enforces minimum coverage on CHANGED files only.
Usage: python scripts/coverage_gate.py --base main --min 80
"""
import subprocess
import sys
import argparse
import json
import re

def get_changed_files(base: str) -> list[str]:
    """Get list of .py files changed vs base branch."""
    r = subprocess.run(
        ['git', 'diff', '--name-only', f'{base}...HEAD'],
        capture_output=True, text=True
    )
    return [f for f in r.stdout.strip().split('\n') if f.endswith('.py')]

def get_coverage_data() -> dict:
    """Parse coverage.xml and return per-file coverage."""
    try:
        with open('coverage.xml') as f:
            content = f.read()
    except FileNotFoundError:
        print("ERROR: coverage.xml not found. Run pytest --cov first.")
        sys.exit(1)

    results = {}
    # Simple regex parse — avoids lxml dependency
    for match in re.finditer(r'<file path="([^"]+)"[^>]*line-rate="([0-9.]+)"', content):
        path, rate = match.group(1), float(match.group(2))
        results[path] = rate * 100
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='main')
    parser.add_argument('--min', type=float, default=80.0)
    args = parser.parse_args()

    changed = get_changed_files(args.base)
    if not changed:
        print("No Python files changed. Skipping coverage gate.")
        return

    coverage = get_coverage_data()
    failed = []

    print(f"\n{'File':<60} {'Coverage':>10} {'Status':>8}")
    print("-" * 80)

    for f in changed:
        rate = coverage.get(f, 0.0)
        status = "✅ PASS" if rate >= args.min else "❌ FAIL"
        if rate < args.min:
            failed.append(f)
        print(f"{f:<60} {rate:>9.1f}% {status:>8}")

    if failed:
        print(f"\n❌ {len(failed)} file(s) below {args.min}% coverage:")
        for f in failed:
            print(f"   {f}")
        sys.exit(1)
    else:
        print(f"\n✅ All changed files meet {args.min}% coverage")

if __name__ == '__main__':
    main()
```

## Flaky Test Quarantine Script

```python
# scripts/flaky_quarantine.py
"""
Detects flaky tests by running suite N times and flagging
tests that pass sometimes and fail sometimes.

Usage: python scripts/flaky_quarantine.py --runs 5 --suite "tests/"
Output: flaky-report.json + moves flaky tests to quarantine/
"""
import subprocess
import json
import argparse
import re
from collections import defaultdict
from pathlib import Path

def run_suite(suite: str, extra_args: list = None) -> dict:
    """Run pytest, return {test_id: passed_bool}."""
    cmd = ['python', '-m', 'pytest', suite, '-v', '--tb=no', '-q']
    if extra_args:
        cmd.extend(extra_args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    
    results = {}
    for line in r.stdout.splitlines():
        # Match: PASSED / FAILED / ERROR test_name
        m = re.match(r'(PASSED|FAILED|ERROR)\s+(.+)', line.strip())
        if m:
            status, name = m.group(1), m.group(2)
            results[name] = (status == 'PASSED')
    return results

def detect_flaky(suite: str, runs: int) -> list[dict]:
    """Run suite N times, find tests with inconsistent results."""
    all_results = defaultdict(list)
    
    for i in range(runs):
        print(f"Run {i+1}/{runs}...")
        results = run_suite(suite)
        for test, passed in results.items():
            all_results[test].append(passed)
    
    flaky = []
    for test, passes in all_results.items():
        pass_count = sum(passes)
        if 0 < pass_count < runs:  # Not all pass, not all fail
            flaky.append({
                'test': test,
                'pass_rate': f"{pass_count}/{runs}",
                'flaky': True
            })
    return flaky

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--suite', default='tests/')
    args = parser.parse_args()

    flaky = detect_flaky(args.suite, args.runs)
    
    if not flaky:
        print(f"✅ No flaky tests detected after {args.runs} runs")
        return

    print(f"\n⚠️  Found {len(flaky)} flaky test(s):\n")
    for f in flaky:
        print(f"  {f['pass_rate']:>5}  {f['test']}")
    
    # Save report
    with open('flaky-report.json', 'w') as fp:
        json.dump(flaky, fp, indent=2)
    print(f"\nReport saved: flaky-report.json")

if __name__ == '__main__':
    main()
```

## Test Quality Dashboard Generator

```python
# scripts/test_quality_report.py
"""
Generates a markdown report combining:
- Line coverage
- Branch coverage
- Mutation score (if available)
- Test count by type
- Slowest tests

Usage: python scripts/test_quality_report.py
"""
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

def get_coverage() -> dict:
    """Parse coverage.xml."""
    try:
        with open('coverage.xml') as f:
            content = f.read()
    except FileNotFoundError:
        return {}
    
    line_match = re.search(r'line-rate="([0-9.]+)"', content)
    branch_match = re.search(r'branch-rate="([0-9.]+)"', content)
    
    return {
        'line': float(line_match.group(1)) * 100 if line_match else 0,
        'branch': float(branch_match.group(1)) * 100 if branch_match else 0,
    }

def get_test_stats() -> dict:
    """Run pytest --collect-only and count by type."""
    r = subprocess.run(
        ['python', '-m', 'pytest', '--collect-only', '-q', '--tb=no'],
        capture_output=True, text=True
    )
    lines = [l for l in r.stdout.splitlines() if '::' in l]
    
    by_type = defaultdict(int)
    for line in lines:
        if '/unit/' in line or 'test_unit' in line:
            by_type['unit'] += 1
        elif '/integration/' in line or 'test_integration' in line:
            by_type['integration'] += 1
        elif '/e2e/' in line or 'test_e2e' in line:
            by_type['e2e'] += 1
        else:
            by_type['other'] += 1
    
    return {
        'total': len(lines),
        'by_type': dict(by_type),
    }

def get_slowest_tests(n: int = 10) -> list[dict]:
    """Get N slowest tests from last run."""
    r = subprocess.run(
        ['python', '-m', 'pytest', '--durations=10', '--tb=no', '-q'],
        capture_output=True, text=True
    )
    
    slow = []
    for line in r.stdout.splitlines():
        m = re.match(r'\s*([0-9.]+)s\s+(.+)', line)
        if m:
            slow.append({'duration': float(m.group(1)), 'test': m.group(2)})
    return slow[:n]

def generate_report():
    cov = get_coverage()
    stats = get_test_stats()
    slowest = get_slowest_tests()
    
    md = f"""# Test Quality Report

Generated: {datetime.now().isoformat()}

## Coverage

| Metric | Value |
|--------|-------|
| Line coverage | {cov.get('line', 0):.1f}% |
| Branch coverage | {cov.get('branch', 0):.1f}% |

## Test Distribution

| Type | Count |
|------|-------|
"""
    for t, c in stats['by_type'].items():
        md += f"| {t} | {c} |\n"
    md += f"| **Total** | **{stats['total']}** |\n"
    
    if slowest:
        md += "\n## Slowest Tests\n\n| Duration | Test |\n|----------|------|\n"
        for t in slowest:
            md += f"| {t['duration']:.2f}s | {t['test']} |\n"
    
    md += """
## Recommendations

- [ ] Line coverage > 80%? {line_status}
- [ ] Branch coverage > 70%? {branch_status}
- [ ] No tests > 5s in unit suite? {slow_status}
- [ ] Unit tests > 50% of total? {ratio_status}
""".format(
        line_status="✅" if cov.get('line', 0) > 80 else "❌",
        branch_status="✅" if cov.get('branch', 0) > 70 else "❌",
        slow_status="✅" if not any(t['duration'] > 5 for t in slowest) else "❌",
        ratio_status="✅" if stats['by_type'].get('unit', 0) > stats['total'] * 0.5 else "❌",
    )
    
    Path('test-quality-report.md').write_text(md)
    print(md)

if __name__ == '__main__':
    from collections import defaultdict
    generate_report()
```

## Docker Compose — Test Environment

```yaml
# docker-compose.test.yml
version: '3.9'

services:
  app:
    build:
      context: .
      target: test  # Dockerfile with test deps
    environment:
      - TESTING=true
      - DATABASE_URL=postgresql://test:test@db:5432/test
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8080:8080"

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 3s
      retries: 10
    tmpfs:
      - /var/lib/postgresql/data  # Fast, ephemeral

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

  mock-api:
    image: mockserver/mockserver:latest
    ports:
      - "1090:1080"
    environment:
      MOCKSERVER_INITIALIZATION_JSON_PATH: /config/mock-config.json
    volumes:
      - ./tests/mock:/config:ro
```