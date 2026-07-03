# openwiki — LangChain Auto-Documentation CLI

**URL:** https://github.com/langchain-ai/openwiki
**Stars:** ~1,568 (148/day) | **Age:** 11 days | **Language:** TypeScript
**Topics:** documentation, cli, codebase, langchain

## Summary
OpenWiki is a CLI that writes and maintains documentation for your codebase, built specifically for agents. Analyzes source code, generates documentation, keeps it updated.

## What to take
- **Agent-generated documentation**: CLI that reads codebase and produces docs
- **Maintenance pattern**: docs auto-update when code changes
- **Agent-first format**: documentation structured for agent consumption, not just human reading
- **LangChain integration**: built on LangChain framework for LLM orchestration

## Applicability
- **Vetka_dwg**: auto-generate docs for pipeline, vision, mapping modules — currently has manual docs/v3/
- **MPT**: auto-document Django controllers, services
- **PIVOBOT**: document bot.js (68KB), services.js (40KB) — large files need docs
- **geo-converter**: document 135KB monolith — critical need
- **FAMILY_TREE**: document worker (58KB), client-side JS modules
- **DBDPerksAddonReveal**: document CLIP/OpenCV pipeline
- **Hermes Agent**: auto-document skills, generate SKILL.md from code