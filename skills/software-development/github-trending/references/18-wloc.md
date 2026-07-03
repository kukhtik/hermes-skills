# wloc — iOS GPS Spoofing via WiFi/Cell Towers

**URL:** https://github.com/Yu9191/wloc
**Stars:** ~2,674 (286/day) | **Age:** 9 days | **Language:** JavaScript
**Topics:** gps, ios, wifi-positioning, location

## Summary
Modifies Apple network location service (WiFi/cell tower) return coordinates. Enables iOS network location spoofing — select point on online map, no manual coordinates needed.

## What to take
- **WiFi/cell positioning internals**: how iOS determines location from WiFi APs + cell towers
- **Location service interception**: kernel-level modification of location API responses
- **Coordinate validation**: understanding of how mobile OS validates GPS vs network location

## Applicability
- **geo-converter**: understanding of WiFi/cell-based positioning systems, coordinate validation, reverse engineering of location APIs
- **Vetka_dwg**: GPS coordinate handling — understanding of how mobile devices report location
- **MPT / PIVOBOT / FAMILY_TREE / DBDPerksAddonReveal**: — нет прямого применения