# Track 07 — scientific imaging from inspectable evidence

**Status:** source authored, native CI pending. **Owner:** CiteLattice science-scene contracts and static/interactive output.

## Scope

Implement deterministic, evidence-linked scientific figures from authoritative typed outputs while respecting source coverage, model uncertainty, licensing, and accessible alternatives. The first vertical slice is annual publication production; complex networks, dimensionality reduction and cross-domain policy/funding scenes are later.

## Requirements and quality

- CL-007: every quantitative mark has a table revision and exact source row key or an aggregate membership digest.
- CL-013: emit a standards-based Vega-Lite v5 specification alongside static SVG and an accessible exact-count table.
- CL-014: no source text/hidden restricted metadata in SVG, tooltip, Vega-Lite data, caches or workbook exports.
- CL-015: scientific scene version changes when provenance/method/population changes; renderer version changes only for layout/style.
- Reject values beyond exact IEEE-754 safe integer when browser numeric marks would otherwise round, while preserving exact counts in typed tables.
- No first-N cropping; reject excess years with an explicit mark budget, then qualify an aggregated semantic zoom adapter with membership conservation.
- Explicitly separate statistical, source-coverage, entity-resolution, model and layout uncertainty.
- Compare user understanding, misleading-change detection, accessibility, resource use and independent geometry checks against ordinary plots before superiority claims.

The first slice is not a substitute for Vega-Lite validation against an independent renderer, accessibility evaluation or quantitative geometry audit outside the generating code.
