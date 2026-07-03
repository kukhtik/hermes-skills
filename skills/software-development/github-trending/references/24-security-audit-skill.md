# security-audit-skill — Cloudflare 6-Phase Security Auditor

**URL:** https://github.com/cloudflare/security-audit-skill
**Stars:** ~2,244 (150/day) | **Age:** 15 days | **Language:** JavaScript
**Topics:** security, audit, agent-skills, coding-agents

## Summary
A coding-agent skill that turns any agent into a security auditor. Orchestrates multiple parallel agents through a six-phase pipeline: recon, hunting, validation, reporting, structured output, and remediation.

## What to take
- **6-phase security pipeline**: recon → hunting → validation → reporting → structured output → remediation
- **Parallel agent orchestration**: multiple agents running security checks simultaneously
- **Structured output format**: security findings as machine-readable JSON
- **Skill-based security**: security audit as a composable agent skill

## Applicability
- **lean-testing**: security testing methodology — adopt 6-phase pipeline as reference
- **requesting-code-review skill**: integrate security audit phase into pre-commit review
- **Vetka_dwg**: audit file upload paths, API endpoints, template parsing
- **MPT**: audit Django REST endpoints, Redis access, LLM API keys
- **PIVOBOT**: audit Telegram bot input validation, D1 SQL injection
- **FAMILY_TREE**: audit D1 SQL, worker API, client-side data handling
- **geo-converter / DBDPerksAddonReveal**: audit file parsing, coordinate input validation