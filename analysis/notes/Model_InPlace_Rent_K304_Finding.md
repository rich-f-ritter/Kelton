# Model finding — in-place contract rent ($1,510) is inflated by one unit (K304)

**Question:** Why does the TMG model show in-place contract rents of $1,510?

## Where the number lives
`Assumptions!K100` ("Total / Weighted Avg", header **K49 = "Avg Contracted Rent"**) = **$1,510.42**.
- Each floor-plan row: `K = AVERAGEIFS(tblRentRoll[Contractual Rent], tblRentRoll[Floor Plan], plan)`
  — the average `Contractual Rent` from the pasted rent roll (**RR Dump**) for that plan.
- Total: `K100 = SUMPRODUCT(K50:K99, F50:F99) / F100` — the per-plan averages **weighted by total
  units (col F, all 240)**.

| Plan | Units | Avg Contract Rent (model) |
|---|---|---|
| 1A Hansel (1BR) | 42 | $1,309 |
| 1B Gilson (1BR) | 42 | $1,332 |
| 2A Pahvant (2BR) | 84 | $1,512 |
| 2B Stansbury (2BR) | 48 | $1,536 |
| 3A Wasatch (3BR) | 24 | **$2,117**  ← inflated |
| **Weighted avg** | **240** | **$1,510** |

## Root cause: unit K304 = $8,143
In the **RR Dump**, unit **K304** (3A-Wasatch, 3BR) carries `Contractual Rent = $8,143`
(and `New Lease Rent = $8,143`). The other 22 occupied 3BRs run $1,695–$2,045.
- 3A average **with** K304 = **$2,117**  (23 units)
- 3A average **without** K304 = **$1,843.09**  (22 units) — ties the RR-T12 intake exactly.

$8,143 is not supported by the source rent roll. In `Rent_Roll_2026-06-16.xlsx`, K304 shows
**market rent $2,045** and **no base "Resident Rent" charge line at all** — only Internet/Cable
$109 + Pest $2. So the unit either is a **staff/model/non-revenue unit** (base rent not billed)
or its base-rent line dropped from the export; either way the model's **$8,143 is a bad value.**

## Impact
- Correcting K304 → 3A avg $1,843 → blended in-place contract rent = **~$1,483** (matches the
  RR-T12 intake's $1,483 contract-rent tie).
- Overstatement: **~$27/unit → ~$79k/yr** of overstated gross/potential contract rent, which
  flows into AGPR/GPR and the revenue base (and value at the cap rate).
- Secondary: the same $8,143 sits in `New Lease Rent`, so check it hasn't leaked into any
  last-5 new-lease / GPR-growth calc (the Assumptions L5 column read a sane $1,807, so that
  path looks unaffected — but verify wherever RR Dump `New Lease Rent` is consumed).

## Fix
In `RR Dump`, correct K304's `Contractual Rent` (and `New Lease Rent`) to the unit's true rent —
or mark it **non-revenue** if it's a staff/model unit. Then `Assumptions!K100` → ~$1,483.
Confirm what K304 actually is (occupied market lease vs staff/model) before choosing the value.
