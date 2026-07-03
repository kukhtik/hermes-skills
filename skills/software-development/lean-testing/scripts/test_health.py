#!/usr/bin/env python3
"""
Test suite health checker.

Analyzes a pytest suite and reports:
- Test count by type (unit/integration/e2e)
- Slowest tests (>5s flagged)
- Duplicate test names
- Tests without assertions
- Coverage gaps (files with 0% coverage)
- Flaky test candidates (if run N times)

Usage:
    python scripts/test_health.py --suite tests/ --runs 3
    python scripts/test_health.py --suite tests/unit/ --check-slow
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


# ============================================================
# Colors (ANSI)
# ============================================================
class C:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def color(text, color_code):
    return f"{color_code}{text}{C.END}"


# ============================================================
# Test Collection Analysis
# ============================================================

def collect_tests(suite_path: str) -> list[dict]:
    """Collect all tests, return list of {name, file, type}."""
    r = subprocess.run(
        ['python', '-m', 'pytest', suite_path, '--collect-only', '-q', '--tb=no'],
        capture_output=True, text=True
    )
    
    tests = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if '::' not in line:
            continue
        
        parts = line.split('::')
        filepath = parts[0]
        test_name = '::'.join(parts[1:])
        
        # Classify
        if '/unit/' in filepath or 'test_unit' in filepath:
            test_type = 'unit'
        elif '/integration/' in filepath or 'test_integration' in filepath:
            test_type = 'integration'
        elif '/e2e/' in filepath or 'test_e2e' in filepath:
            test_type = 'e2e'
        elif '/smoke/' in filepath or 'test_smoke' in filepath:
            test_type = 'smoke'
        else:
            test_type = 'other'
        
        tests.append({
            'name': line,
            'file': filepath,
            'test': test_name,
            'type': test_type,
        })
    
    return tests


def check_duplicates(tests: list[dict]) -> list[str]:
    """Find tests with duplicate names (not paths)."""
    names = [t['test'] for t in tests]
    dups = [name for name, count in Counter(names).items() if count > 1]
    return dups


def check_no_assertions(tests: list[dict]) -> list[str]:
    """Find test files with tests that have no assert statements."""
    # Group by file
    by_file = defaultdict(list)
    for t in tests:
        by_file[t['file']].append(t['test'])
    
    no_assert = []
    for filepath, test_names in by_file.items():
        if not os.path.exists(filepath):
            continue
        try:
            content = Path(filepath).read_text()
        except Exception:
            continue
        
        # Simple check: any assert or pytest.raises in file
        has_assert = bool(re.search(r'\bassert\b|\bpytest\.raises\b|\bpytest\.warns\b', content))
        if not has_assert and test_names:
            no_assert.append(filepath)
    
    return no_assert


# ============================================================
# Slow Test Detection
# ============================================================

def find_slow_tests(suite_path: str, threshold: float = 5.0, top_n: int = 20) -> list[dict]:
    """Run suite and report tests slower than threshold."""
    print(color(f"\n⏱  Running suite to measure timings (threshold: {threshold}s)...", C.BLUE))
    
    r = subprocess.run(
        ['python', '-m', 'pytest', suite_path, f'--durations={top_n}', '--tb=no', '-q'],
        capture_output=True, text=True, timeout=600
    )
    
    slow = []
    for line in r.stdout.splitlines():
        m = re.match(r'\s*([0-9.]+)s\s+(.+)', line)
        if m:
            duration = float(m.group(1))
            name = m.group(2).strip()
            if duration >= threshold:
                slow.append({'duration': duration, 'test': name})
    
    return slow


# ============================================================
# Flaky Test Detection
# ============================================================

def detect_flaky(suite_path: str, runs: int = 3) -> list[dict]:
    """Run suite N times, detect tests with inconsistent pass/fail."""
    print(color(f"\n🔁 Running suite {runs} times to detect flaky tests...", C.BLUE))
    
    results = defaultdict(list)
    
    for i in range(runs):
        print(f"  Run {i+1}/{runs}...", end=' ', flush=True)
        r = subprocess.run(
            ['python', '-m', 'pytest', suite_path, '-v', '--tb=no', '-q'],
            capture_output=True, text=True, timeout=600
        )
        
        # Parse results
        for line in r.stdout.splitlines():
            m = re.match(r'(PASSED|FAILED|ERROR)\s+(.+)', line.strip())
            if m:
                status, name = m.group(1), m.group(2)
                results[name].append(status)
        
        passed = sum(1 for s in r.stdout.splitlines() if 'PASSED' in s)
        print(f"{passed} passed")
    
    # Find flaky
    flaky = []
    for name, statuses in results.items():
        unique = set(statuses)
        if len(unique) > 1:
            flaky.append({
                'test': name,
                'results': statuses,
                'pass_rate': f"{statuses.count('PASSED')}/{len(statuses)}",
            })
    
    return flaky


# ============================================================
# Coverage Gap Analysis
# ============================================================

def coverage_gaps(src_dir: str = 'src') -> list[str]:
    """Find source files with 0% coverage."""
    try:
        with open('coverage.xml') as f:
            content = f.read()
    except FileNotFoundError:
        return []
    
    zero_coverage = []
    for match in re.finditer(r'<file path="([^"]+)"[^>]*line-rate="0\.0"', content):
        zero_coverage.append(match.group(1))
    
    return zero_coverage


# ============================================================
# Report
# ============================================================

def generate_report(tests, duplicates, no_assert, slow, flaky, gaps, runs):
    """Generate and print health report."""
    print("\n" + "=" * 70)
    print(color(f" {C.BOLD}TEST SUITE HEALTH REPORT{C.END}", C.BLUE))
    print("=" * 70)
    
    # Summary
    by_type = Counter(t['type'] for t in tests)
    total = len(tests)
    
    print(f"\n{C.BOLD}📊 Summary{C.END}")
    print(f"  Total tests: {total}")
    for t in ['unit', 'integration', 'e2e', 'smoke', 'other']:
        count = by_type.get(t, 0)
        pct = (count / total * 100) if total else 0
        bar = '█' * int(pct / 2)
        print(f"  {t:>12}: {count:>5} ({pct:>5.1f}%) {bar}")
    
    # Distribution check
    unit_pct = by_type.get('unit', 0) / total * 100 if total else 0
    e2e_pct = by_type.get('e2e', 0) / total * 100 if total else 0
    print(f"\n  Unit ratio: {unit_pct:.0f}%", end=' ')
    print(color("✅" if unit_pct > 50 else "⚠️  <50%", C.GREEN if unit_pct > 50 else C.YELLOW))
    print(f"  E2E ratio:  {e2e_pct:.0f}%", end=' ')
    print(color("✅" if e2e_pct < 15 else "⚠️  >15% (ice cream cone!)", C.GREEN if e2e_pct < 15 else C.RED))
    
    # Duplicates
    if duplicates:
        print(f"\n{C.BOLD}🔁 Duplicate test names{C.END}")
        print(color(f"  Found {len(duplicates)} duplicates:", C.YELLOW))
        for d in duplicates[:10]:
            print(f"    {d}")
    else:
        print(f"\n{C.BOLD}🔁 Duplicate test names{C.END} {color('✅ None', C.GREEN)}")
    
    # No assertions
    if no_assert:
        print(f"\n{C.BOLD}🔍 Files without assertions{C.END}")
        print(color(f"  Found {len(no_assert)} file(s):", C.RED))
        for f in no_assert[:10]:
            print(f"    {f}")
    else:
        print(f"\n{C.BOLD}🔍 Files without assertions{C.END} {color('✅ All have assertions', C.GREEN)}")
    
    # Slow tests
    if slow:
        print(f"\n{C.BOLD}⏱  Slow tests (>{5}s){C.END}")
        print(color(f"  Found {len(slow)} slow test(s):", C.YELLOW))
        for t in slow[:10]:
            print(f"    {t['duration']:>6.2f}s  {t['test']}")
    else:
        print(f"\n{C.BOLD}⏱  Slow tests{C.END} {color('✅ All under threshold', C.GREEN)}")
    
    # Flaky
    if runs > 1 and flaky:
        print(f"\n{C.BOLD}🎲 Flaky tests{C.END}")
        print(color(f"  Found {len(flaky)} flaky test(s):", C.RED))
        for f in flaky[:10]:
            print(f"    {f['pass_rate']:>5}  {f['test']}")
    elif runs > 1:
        print(f"\n{C.BOLD}🎲 Flaky tests{C.END} {color('✅ None detected', C.GREEN)}")
    
    # Coverage gaps
    if gaps:
        print(f"\n{C.BOLD}📉 Zero-coverage files{C.END}")
        print(color(f"  Found {len(gaps)} file(s) with 0% coverage:", C.RED))
        for g in gaps[:10]:
            print(f"    {g}")
    else:
        print(f"\n{C.BOLD}📉 Zero-coverage files{C.END} {color('✅ None or no coverage.xml', C.GREEN)}")
    
    # Overall health score
    score = 100
    if duplicates:
        score -= 10
    if no_assert:
        score -= 20
    if slow:
        score -= 15
    if runs > 1 and flaky:
        score -= 25
    if gaps:
        score -= 15
    if unit_pct < 50:
        score -= 15
    if e2e_pct > 15:
        score -= 10
    
    score = max(0, score)
    grade = 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F'
    grade_color = C.GREEN if score >= 75 else C.YELLOW if score >= 60 else C.RED
    
    print(f"\n{'='*70}")
    print(f" {C.BOLD}OVERALL HEALTH: {color(f'{score}/100 (Grade: {grade})', grade_color)}{C.END}")
    print(f"{'='*70}\n")
    
    # Save JSON
    report = {
        'total_tests': total,
        'by_type': dict(by_type),
        'duplicates': duplicates,
        'no_assertion_files': no_assert,
        'slow_tests': slow,
        'flaky_tests': flaky if runs > 1 else [],
        'coverage_gaps': gaps,
        'health_score': score,
        'grade': grade,
    }
    with open('test-health-report.json', 'w') as f:
        json.dump(report, f, indent=2)
    print("Report saved: test-health-report.json")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Test suite health checker')
    parser.add_argument('--suite', default='tests/', help='Test suite path')
    parser.add_argument('--runs', type=int, default=1, help='Number of runs for flaky detection')
    parser.add_argument('--check-slow', action='store_true', help='Run suite to find slow tests')
    parser.add_argument('--slow-threshold', type=float, default=5.0, help='Slow test threshold (seconds)')
    args = parser.parse_args()
    
    print(color("🔍 Analyzing test suite...", C.BLUE))
    
    # Collect
    tests = collect_tests(args.suite)
    if not tests:
        print(color("❌ No tests found!", C.RED))
        sys.exit(1)
    
    # Analyze
    duplicates = check_duplicates(tests)
    no_assert = check_no_assertions(tests)
    
    slow = []
    if args.check_slow:
        slow = find_slow_tests(args.suite, args.slow_threshold)
    
    flaky = []
    if args.runs > 1:
        flaky = detect_flaky(args.suite, args.runs)
    
    gaps = coverage_gaps()
    
    # Report
    generate_report(tests, duplicates, no_assert, slow, flaky, gaps, args.runs)


if __name__ == '__main__':
    main()