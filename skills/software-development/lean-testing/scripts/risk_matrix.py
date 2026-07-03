#!/usr/bin/env python3
"""
Risk-based test prioritization matrix.

Helps decide WHERE to invest testing effort based on:
- Impact: how bad is a failure here? (1-5)
- Probability: how likely is a failure? (1-5)
- Complexity: how complex is the code? (1-5)
- Volatility: how often does it change? (1-5)

Risk Score = (Impact × Probability) + (Complexity × Volatility / 2)

Usage:
    python scripts/risk_matrix.py                    # Interactive
    python scripts/risk_matrix.py --config risk.yaml  # From config

Output: risk-matrix.html (visual) + risk-priorities.json (data)
"""

import argparse
import json
import sys
from pathlib import Path

# ============================================================
# Risk Calculation
# ============================================================

def calc_risk(impact, probability, complexity, volatility):
    """Calculate risk score 1-35."""
    base = impact * probability           # 1-25
    modifier = (complexity * volatility) / 2  # 0.5-12.5
    return round(base + modifier, 1)


def risk_level(score):
    """Classify risk level."""
    if score >= 20:
        return "CRITICAL", '\033[91m'  # Red
    elif score >= 12:
        return "HIGH", '\033[93m'      # Yellow
    elif score >= 6:
        return "MEDIUM", '\033[94m'    # Blue
    else:
        return "LOW", '\033[92m'      # Green


# ============================================================
# Default risk items (examples)
# ============================================================

DEFAULT_ITEMS = [
    {
        "name": "Authentication / Authorization",
        "impact": 5, "probability": 3, "complexity": 4, "volatility": 2,
        "notes": "Security critical, moderate change frequency"
    },
    {
        "name": "Data parsing / serialization",
        "impact": 4, "probability": 4, "complexity": 3, "volatility": 3,
        "notes": "Edge cases common, medium complexity"
    },
    {
        "name": "Database migrations",
        "impact": 5, "probability": 2, "complexity": 4, "volatility": 2,
        "notes": "Rare but catastrophic if wrong"
    },
    {
        "name": "Third-party API integration",
        "impact": 3, "probability": 4, "complexity": 2, "volatility": 4,
        "notes": "External changes, rate limits, downtime"
    },
    {
        "name": "UI component rendering",
        "impact": 2, "probability": 3, "complexity": 2, "volatility": 5,
        "notes": "Changes every sprint, low impact if buggy"
    },
    {
        "name": "Background jobs / queues",
        "impact": 4, "probability": 2, "complexity": 4, "volatility": 1,
        "notes": "Stable code, hard to debug when fails"
    },
    {
        "name": "File upload / processing",
        "impact": 3, "probability": 3, "complexity": 3, "volatility": 2,
        "notes": "Security + performance risks"
    },
    {
        "name": "Payment processing",
        "impact": 5, "probability": 2, "complexity": 4, "volatility": 1,
        "notes": "Money = maximum impact"
    },
]


# ============================================================
# HTML Report Generator
# ============================================================

def generate_html(items):
    """Generate visual HTML risk matrix."""
    sorted_items = sorted(items, key=lambda x: calc_risk(
        x['impact'], x['probability'], x['complexity'], x['volatility']
    ), reverse=True)
    
    rows = ""
    for item in sorted_items:
        score = calc_risk(item['impact'], item['probability'],
                         item['complexity'], item['volatility'])
        level, _ = risk_level(score)
        
        color = {
            "CRITICAL": "#ff4444",
            "HIGH": "#ff9900",
            "MEDIUM": "#4488ff",
            "LOW": "#44aa44",
        }[level]
        
        # Priority recommendation
        if level == "CRITICAL":
            action = "Full coverage + property tests + mutation + exploratory"
        elif level == "HIGH":
            action = "High coverage + property tests + exploratory"
        elif level == "MEDIUM":
            action = "Standard coverage + smoke tests"
        else:
            action = "Smoke tests only, low investment"
        
        rows += f"""
        <tr style="border-left: 4px solid {color}">
            <td><strong>{item['name']}</strong></td>
            <td style="text-align:center">{item['impact']}</td>
            <td style="text-align:center">{item['probability']}</td>
            <td style="text-align:center">{item['complexity']}</td>
            <td style="text-align:center">{item['volatility']}</td>
            <td style="text-align:center"><strong style="color:{color}">{score}</strong></td>
            <td style="text-align:center"><span style="color:{color};font-weight:bold">{level}</span></td>
            <td>{action}</td>
            <td style="color:#888">{item.get('notes', '')}</td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Test Risk Prioritization Matrix</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 40px; background: #f8f9fa; }}
h1 {{ color: #333; }}
table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #2c3e50; color: white; font-weight: 600; position: sticky; top: 0; }}
tr:hover {{ background: #f5f5f5; }}
.legend {{ margin: 20px 0; padding: 15px; background: white; border-radius: 8px; }}
.legend span {{ margin-right: 20px; font-weight: bold; }}
</style>
</head>
<body>
<h1>📊 Test Risk Prioritization Matrix</h1>

<div class="legend">
<span style="color:#ff4444">■ CRITICAL (≥20)</span>
<span style="color:#ff9900">■ HIGH (12-19)</span>
<span style="color:#4488ff">■ MEDIUM (6-11)</span>
<span style="color:#44aa44">■ LOW (<6)</span>
</div>

<table>
<thead>
<tr>
    <th>Component</th>
    <th>Impact</th>
    <th>Probability</th>
    <th>Complexity</th>
    <th>Volatility</th>
    <th>Score</th>
    <th>Level</th>
    <th>Recommended Testing</th>
    <th>Notes</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>

<p style="margin-top:20px;color:#888;font-size:0.9em">
Score = (Impact × Probability) + (Complexity × Volatility / 2) &nbsp;|&nbsp;
Generated by lean-testing skill
</p>
</body>
</html>"""
    
    return html


# ============================================================
# Interactive Mode
# ============================================================

def interactive():
    """Interactive risk assessment."""
    items = []
    print("\n📊 Risk-Based Test Prioritization\n")
    print("Rate each component 1-5 for each factor.\n")
    
    while True:
        name = input("Component name (or 'done' to finish): ").strip()
        if name.lower() == 'done' or not name:
            break
        
        try:
            impact = int(input("  Impact (1=minor, 5=catastrophic): "))
            probability = int(input("  Probability (1=rare, 5=very likely): "))
            complexity = int(input("  Complexity (1=trivial, 5=very complex): "))
            volatility = int(input("  Volatility (1=never changes, 5=changes daily): "))
            notes = input("  Notes (optional): ").strip()
            
            if not all(1 <= v <= 5 for v in [impact, probability, complexity, volatility]):
                print("  ⚠️  All values must be 1-5!")
                continue
        except ValueError:
            print("  ⚠️  Please enter numbers 1-5!")
            continue
        
        items.append({
            "name": name,
            "impact": impact,
            "probability": probability,
            "complexity": complexity,
            "volatility": volatility,
            "notes": notes,
        })
        print(f"  ✅ Added: {name}\n")
    
    return items


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Risk-based test prioritization')
    parser.add_argument('--config', help='YAML config with risk items')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--output', default='risk-matrix.html', help='Output HTML file')
    args = parser.parse_args()
    
    # Get items
    if args.interactive:
        items = interactive()
    elif args.config:
        import yaml
        with open(args.config) as f:
            data = yaml.safe_load(f)
        items = data.get('items', DEFAULT_ITEMS)
    else:
        items = DEFAULT_ITEMS
    
    if not items:
        print("No items to analyze!")
        sys.exit(1)
    
    # Calculate and display
    print("\n" + "=" * 90)
    print(f"{'Component':<35} {'Imp':>4} {'Prob':>5} {'Cplx':>5} {'Vol':>4} {'Score':>6} {'Level':<12}")
    print("=" * 90)
    
    sorted_items = sorted(items, key=lambda x: calc_risk(
        x['impact'], x['probability'], x['complexity'], x['volatility']
    ), reverse=True)
    
    for item in sorted_items:
        score = calc_risk(item['impact'], item['probability'],
                         item['complexity'], item['volatility'])
        level, color_code = risk_level(score)
        
        # ANSI color
        END = '\033[0m'
        print(f"{item['name']:<35} {item['impact']:>4} {item['probability']:>5} "
              f"{item['complexity']:>5} {item['volatility']:>4} "
              f"{color_code}{score:>6.1f}  {level:<12}{END}")
    
    print("=" * 90)
    
    # Generate HTML
    html = generate_html(items)
    Path(args.output).write_text(html)
    print(f"\n✅ Visual report: {args.output}")
    
    # Save JSON
    results = []
    for item in sorted_items:
        score = calc_risk(item['impact'], item['probability'],
                         item['complexity'], item['volatility'])
        level, _ = risk_level(score)
        results.append({
            **item,
            'score': score,
            'level': level,
        })
    
    with open('risk-priorities.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Data file: risk-priorities.json")


if __name__ == '__main__':
    main()