# shadcn/improve — Codebase Audit + Agent Plans

**URL:** https://github.com/shadcn/improve
**Stars:** ~6,674 (289/day) | **Age:** 23 days | **Language:** N/A (Markdown/skills)
**Topics:** agent-skills, code-review, planning

## Summary
An agent skill that audits any codebase and writes implementation plans for other agents to execute. Two-phase: audit → plan → execute.

## What to take
- **Audit → Plan → Execute pattern**: one agent audits, writes structured plan, another agent executes
- **Skill format**: markdown-based skills that any coding agent can consume
- **Structured plan output**: plans formatted for agent consumption, not human

## Applicability
- **Hermes Agent**: subagent-driven-development skill — adopt audit→plan pattern
- **lean-testing**: code review automation — agent audits test quality
- **Vetka_dwg / MPT / PIVOBOT / geo-converter / FAMILY_TREE**: automated code review before merge
- **DBDPerksAddonReveal**: audit pipeline code for improvements