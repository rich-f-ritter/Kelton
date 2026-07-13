# The Kelton — Supply Chart Summary

**Built:** 2026-07-13 · Skill: `supply-chart` · Bundle: full CoStar (roster + overall + per-property) + RealPage + HelloData 5-mi. Subject rent history extended pre-HelloData with `--realpage-subject-rents` (RealPage_Provo_Historical_Rent_and_Occ.xlsx).

## Deliverables (this folder)
- `The_Kelton__Supply_Chart.xlsx` — Competitive Analysis, Supply & Absorption, Reconciliation Log
- `The_Kelton__Map.html` — self-contained Leaflet satellite map (16 comps + subject, gold 5-mi ring, 0 CDN refs)
- `The_Kelton__Supply_Chart__pipeline_dates_TEMPLATE.csv` — empty (no undated proposed deals)
- `The_Kelton__Supply_Chart__diligence_TEMPLATE.csv` — opt-in diligence template (not run)

## Current inventory
**7,632 units** (5-mi, CoStar Q2 2026, latest complete quarter; 2026 Q3 QTD partial excluded from TTM). Headline occupancy **88.0%**, depressed by the Sanctuary lease-up; stabilized comps run ~93–95%.

## Roster — 16 comps, all delivery quarters pinned from CoStar per-property analytics
- **14 Stabilized/Stabilizing** (2,674u) · **2 Leasing Up** (871u) · **0 Under Construction** · **0 Proposed**
- Leasing up: **Sanctuary** 519u (Q1 2026, ~20% occ, ~26 leases/mo HD) · **Solhavn** 352u (Q3 2024; HD cumulative lease-up ~100% vs stale vendor 70%).

## Trailing supply (CoStar deliveries, TTM windows)
-Y4 795 · -Y3 1,000 · -Y2 **1,310 (peak)** · -Y1 386 · **Y0 528** (Beacon Cove 9 + Sanctuary 519).

## Forward pipeline: ZERO
CoStar UC series = 0 as of Q2 2026 (Sanctuary was the last UC unit, delivered Q1 2026); roster carries 0 UC / 0 proposed; UC-vs-CoStar reconciliation ties at 0.
**Caveat:** the RealPage pull is the Grid-Performance shape (no Property Status column) — it contributed occupancy/effective-rent cross-checks but cannot independently flag pipeline, so latent/pre-planned supply would only surface via the opt-in `--diligence` scan (not run).

## Tie-out result
**Y0 ties to the unit** (528 = 528). Historical windows differ only in the benign direction (CoStar over roster): +87 / +6 / +107 / +34u (234 total), all sub-50/unnamed product the 50-unit export can't itemize; subject's 240u auto-added-back in -Y4. No roster-over → no mis-dated/double-counted 50+ comp; no RealPage-only supply. The ⚠ console flag is the generic non-zero-residual prompt — verified benign.

## Demand & re-stabilization
Base demand = **725 u/yr** (trailing-3-yr CoStar avg); Bear 350, Bull 1,100 (actual trailing absorption -Y3/-Y2/-Y1 = 871/920/989, Y0 = 258). With zero forward supply, inventory stays flat at 7,632 and the ~534-unit gap to 95% target is essentially just Sanctuary.
**Under Base, occupancy re-stabilizes to 95% by Y1; under Bear by Y2; Bull immediately.** Favorable supply setup.

## Subject vs market
Delivered -Y4, leased up 5%→64%→92%→96%, now stabilized. **Y0 (HD mix-weighted): market rent ≈ $1,588, effective ≈ $1,545, occupancy ≈ 93.6%.** Rent sits **below the comp median $1,724** (range $1,424–$2,496) — relative-value position vs 2022–26 new builds; occupancy 93.6% is above the 88.0% headline (Sanctuary-dragged) and in line with stabilized comps. Rent-history source: RealPage -Y4/-Y3, HelloData -Y2→Y0.

## Open items
1. Zero vendor pipeline — surfacing latent supply needs the opt-in `--diligence` shadow-supply web research (available, not run).
2. RealPage = Grid-Performance shape (no status column) → no independent pipeline detection; relied on CoStar UC=0.
3. Subject Y0→Y6 rent/occ cells are dormant `IFERROR` links to `Cash Flow (Annual)` (fall back to HD Y0 values above); resolve when tabs are dragged into the TMG model.
4. Map placed all 17 pins (16 comps + subject) — no missing coordinates.
