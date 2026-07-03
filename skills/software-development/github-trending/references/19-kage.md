# kage — Website Cloner with Headless Chrome

**URL:** https://github.com/tamnd/kage
**Stars:** ~2,660 (139/day) | **Age:** 19 days | **Language:** Go
**Topics:** web-archival, headless-chrome, dom-snapshot

## Summary
kage ("shadow") clones a website into a folder for offline browsing. Opens each page in real headless Chrome, waits for page to settle, snapshots DOM, strips scripts.

## What to take
- **Headless Chrome DOM snapshot**: reliable page capture after JS execution
- **Script stripping**: remove all `<script>` tags for safe offline viewing
- **Page settle detection**: wait for network idle / DOM stable before snapshot
- **Go + Chrome DevTools Protocol**: CDP integration for page automation

## Applicability
- **FAMILY_TREE**: snapshot testing — DOM snapshot approach for visual regression
- **Hermes Agent (dogfood skill)**: web QA — clone site for offline testing, visual comparison
- **Vetka_dwg / MPT / PIVOBOT / geo-converter / DBDPerksAddonReveal**: — нет прямого применения