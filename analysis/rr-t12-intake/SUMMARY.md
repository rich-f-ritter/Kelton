# The Kelton — Underwriting Intake Summary

**Property:** The Kelton Apartments, 301 S 1100 W, American Fork, UT 84003
**Operator:** Neighborly Communities (ResMan platform)
**Generated:** 2026-07-13 · RR-T12 Processor · **AUDIT mode**
**Workbook:** `analysis/rr-t12-intake/The_Kelton__Underwriting_Intake.xlsx`

---

## 1. Inputs stitched & period covered

| Input | File | Role |
|---|---|---|
| RedIQ operating statement | `Operating_Statement_RedIQ_thru_2026-05.xlsx` | **Audit source** (Overview + Code/Category/Line-Item detail → auto-triggered AUDIT mode) |
| Native operator T12 | `Trailing_PL_Detail_2026-05-31.xlsx` (Neighborly/ResMan) | **NOI cross-tie** only (not stitched into the audit) |
| Rent roll | `Rent_Roll_2026-06-16.xlsx` (ResMan, as-of 6/15–6/16/2026) | 240 units, unit mix, occupancy, AGPR tie |
| HelloData Unit Details | `HelloData_Kelton_subject_only_2026-07-13.csv` | 371 listing records / 183 unique units; joined to RR by unit # |

**Operating period:** Jun 2025 – May 2026 (trailing 12 months). Both financials cover exactly this T12 window.

**Mode:** AUDIT (a RedIQ export was present). The skill audits RedIQ's own categorization rather than rebuilding the OS. Recalc is optional in audit mode (headline figures are static values; only trivial within-sheet SUMs are formulas, computed by Excel on open). 0 formula-error cells in the workbook.

---

## 2. Headline financials (T12, RedIQ-standardized)

| Metric | Value |
|---|---|
| **Effective Gross Revenue** | **$4,850,394** |
| **Operating Expenses** | **$1,841,644** |
| **Net Operating Income** | **$3,008,750** |
| Operating margin | 62.0% |
| Occupancy (by unit) | **93.75%** — 225 occupied / 15 vacant / 0 non-revenue of 240 |
| Total rentable SF | 233,406 |

---

## 3. RedIQ Audit exceptions (2 total: 1 HIGH · 0 MED · 1 LOW)

- **HIGH — `41120 DELINQUENT RENT` (−$22,671/yr).** RedIQ codes it `cl` (Collection Loss/Bad Debt, in EGR **above** NOI); our read suggests `onoe` (Other Non-Operating, **below** NOI), which would raise NOI ~$22.7k. **Assessment: RedIQ's `cl` is the conventional/correct treatment** — delinquent rent IS collection loss, an operating revenue reduction; our `onoe` is the likely over-flag (audit is a first-pass). **Recommend keeping RedIQ's `cl`.**
- **LOW — `42100 MTM FEE INCOME` (+$5,849/yr).** RedIQ `OI` vs our `Rentinc`. NOI-neutral (both in EGR). Operator-dependent judgment call; optional.

Full line-by-line comparison is on the **RedIQ Categorized** tab.

---

## 4. NOI cross-tie — RedIQ vs the operator's own T12  ✓ TIES

**RedIQ NOI $3,008,750  vs  operator-T12 re-standardized NOI $3,020,832 → Δ −$12,082 (0.4%) ✓** (RedIQ Audit tab header).

### Material finding — the operator's printed "NOI" is overstated by $353k/yr
The operator's own **"NET OPERATING INCOME" line reads $3,361,990** — **overstating true NOI by $353,240/yr (~12%)** because Neighborly books **property Taxes & Insurance ($353,240) BELOW its NOI line**. RedIQ correctly pulls taxes/insurance into OpEx. Verified to the penny:

- Operator **TOTAL INCOME** $4,850,393.92 **= RedIQ EGR** (exact)
- Operator **TOTAL EXPENSE** $1,488,404.22 **+ Taxes/Ins** $353,239.55 **= RedIQ OpEx** $1,841,643.77 (exact)
- Operator **"NOI"** $3,361,989.70 **− Taxes/Ins** $353,239.55 **= RedIQ NOI** $3,008,750.15 (exact)

**Underwrite to the standardized/RedIQ NOI ($3,008,750), NOT the operator's stated $3,361,990.**

---

## 5. Rent-roll ↔ T12 reconciliation

| Tie-out | Rent Roll | T12 (latest mo / ann.) | Var |
|---|---|---|---|
| Gross market rent (asking), monthly | $399,280 | $399,622 | 0.09% |
| **Contract rent (occupied), monthly** | **$332,372** | **$335,516** | **0.9%** |
| Gross Potential Rent (all 240 units), monthly | $356,113 | $350,769 | 1.5% |
| **T1 AGPR, annualized** | **$4.27M** | **$4.21M** | **1.5%** |
| Other Income (recurring), monthly | $36,452 | $67,031 | large (see Flag #3) |

- **Charge → T12 placement (empirical):** base "Resident Rent" ties to T12 Rental Income (contract); Internet/Cable ties to `42190 TVCABLE INCOME` (Other Income). One unit's base rent is billed under a charge literally named "Rent" ($1,525/mo) — correctly contract; the $-match test coincidentally flagged it against Pet Rent (immaterial).
- **Cross-checks:** Parking — RR 195 units $8,420/mo ↔ T12 $8,255/mo (98% on T12). Utility recapture (RUBS) — T12 utility expense $41,028/mo ↔ RUBS/billback income $29,383/mo = **72% recaptured** (water/sewer alone 142%).

---

## 6. Market-rent indicators (true signal)

| Indicator (mix-weighted) | Value |
|---|---|
| **HelloData T90 asking** | **$1,595** |
| **HelloData T90 effective** | **$1,501** |
| **New-lease contract T90 (avg)** | **$1,484** |
| New / renewal leases | 105 / 120 |

Seasonality: executed asking peaks Jun, troughs Sep (~9% spread). HD asking YoY (same month) −0.5% avg over 25 pairs. Per-plan HD T90/T365 asking & effective + HD90 YoY on the Dashboard unit mix; monthly trajectory on Lease Trend.

### Unit mix (5 plans; bed/bath from HelloData)
| Plan | Bed/Bath | Units | Avg SF | Avg Mkt (RR) | Avg Contract |
|---|---|---|---|---|---|
| 1A Hansel | 1/1 | 42 | 694 | $1,442 | $1,309 |
| 1B Gilson | 1/1 | 42 | 793 | $1,542 | $1,332 |
| 2A Pahvant | 2/2 | 84 | 1,024 | $1,692 | $1,512 |
| 2B Stansbury | 2/2 | 48 | 1,114 | $1,742 | $1,536 |
| 3A Wasatch | 3/2 | 24 | 1,311 | $2,012 | $1,843 |
| **Total/Avg** | — | **240** | **973** | **$1,664** | **$1,483** |

---

## 7. HelloData fee decision — shown GROSS, not netted

HD T90 asking ($1,595) sits **$111/mo above** new-lease base ($1,484). Candidate flat fees: Internet/Cable $109 + Pest $2 = $111 (coincides with the gap).

**Decision: HD GROSS — no `--hd-fee-offset` applied.** Per `references/hd_fee_detection.md`: operator is **Neighborly Communities, NOT Greystar** (not a known all-in / "Total Monthly Leasing Price" advertiser); inferring a bundle from rent-roll charges is unreliable; website scraping is blocked. Net only a website-confirmed bundle. The $111 gap is most likely ordinary asking-over-signed premium plus a real Internet/Cable mandatory charge. **Underwriter action:** compare HD's asking for a currently-listed Kelton unit to that unit's base vs "Total Monthly" on the website before any netting.

---

## 8. Open flags for the underwriter

1. **HIGH audit exception** — Delinquent Rent (`cl` vs `onoe`); RedIQ's `cl` likely correct.
2. **Operator "NOI" inflated $353k** — use $3,008,750, not the operator's $3,361,990.
3. **Other Income RR $36k/mo vs T12 $67k/mo** — this ResMan roll's *scheduled* charges omit RUBS/utility reimbursements (`42160 RUBS – Water/Sewer/Trash` ≈ $328,579/yr books on the T12, no per-unit scheduled charge). **Underwrite Other Income and RUBS to the T12, not the rent roll.**
4. **HD fee gap $111** — confirm at website before netting.
5. **Valet Trash Service** ($14/mo) — confirm nets vs trash expense or Other Income.
6. **`DUES & SUBSCRIPTIONS` = $111,506/yr** (coded `GA`) is unusually large — eyeball its contents.

---

## 9. Model paste targets (audit mode)

- **RR Dump** ← `Rent Roll (One-Line)` **A3:M242** (240 unit rows; row 1 headers, row 2 spacer, row 243 TOTAL/AVG — exclude). Bed/Bath (D/E) populated from the HelloData by-unit join.
- **HD Dump** ← `HelloData` **A2:U372** (371 rows; col U = Floorplan Mapped).
- **OS Summary Dump / T12 Dump:** AUDIT mode does not rebuild OS Summary / T12 Categorized — apply the RedIQ Audit code fixes (§3) to the client's existing RedIQ OS/T12 dumps. (Dashboard's generic "HOW TO USE" text still names those tabs; ignore those two lines.)

---

## 10. Parser work done to complete the build (technical note)

Initial build returned `BUILD_INCOMPLETE` (rent roll parsed 0 units); root causes were unrecognized ResMan/Neighborly layouts. Fixes applied to the skill scripts:

- **`intake_lib.parse_rent_roll`** — unit-id column offset (merged Unit cell puts the id one column left of its header); block detection when the charge column is named "Description"/"Amount" (not "Charge"); ResMan footer boundary markers.
- **`account_map`** — base rent billed as "Resident Rent" → `Rentinc`/contract (anchored so "Concession – Resident Rent" stays a concession).
- **`intake_lib.parse_t12`** — native ResMan hierarchical P&L wasn't parsing (0 months): `_month_label` strips trailing "Actual/Budget/Variance" qualifier; coalesce account label across cascading indent columns; space-fused GL split ("40100 RENT INCOME"); exclude Total/Variance/Adjusted summary columns from the GL-number scan (they were mistaken for a GL column → double-counting).
- **`account_map`** — asset/partnership/corporate management fees → non-op (`onoe`); capital-expense section/keyword → `capx` (non-op). Aligns with RedIQ's below-NOI treatment; makes the operator NOI cross-tie tie. Common-line regression check passed.
- **Bed/bath** — added HelloData by-unit join so the One-Line per-unit Bed/Bath populate (240/240).

comp_rev ties to operator TOTAL INCOME to the penny after fixes; audit exceptions unchanged (2).
