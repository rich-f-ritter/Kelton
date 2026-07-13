# The Kelton — Deal Folder

**301 S 1100 W, American Fork, UT 84003** · 240-unit garden-style multifamily

This repository is the working folder for the Kelton acquisition analysis. It holds
every source file provided for the deal, the analysis tooling (skills), and all
work product we generate. Raw inputs live under `data/`; our outputs live under
`analysis/`.

---

## Property snapshot

| Attribute | Value | Source |
|---|---|---|
| Address | 301 S 1100 W, American Fork, UT 84003 | — |
| Units | 240 | CoStar / RealPage / rent roll |
| Unit mix | 84 × 1BR, 132 × 2BR, 24 × 3BR | CoStar Property List |
| Avg unit size | ~972 SF | CoStar / RealPage |
| Year built | 2022 (const. began Jul 2021); RealPage lists 2023 | CoStar / RealPage |
| Stories / style | 3 · Garden | RealPage |
| Class | B (CoStar) / B+ (RealPage) | CoStar / RealPage |
| Developer / Owner | Neighborly Ventures; title entity **MWIC Kelton Commercial LLC** (Mountain West Investment Corp, Salem OR) | CoStar / Utah County |
| Property manager | Neighborly Communities | CoStar / operator reports |
| Market / submarket | Provo–Orem–Lehi · North Utah County / Silicon Slopes (CoStar) · Orem/Lehi (RealPage) | CoStar / RealPage |
| Tax parcels | 15 lots — "Kelton Apartments Phase 1 Plat," serials 44:238:0001–0015 | Utah County |
| Recent asking rent | ~$1,656/unit (~$1.70/SF) | CoStar (2026 Q3 QTD) |
| Recent occupancy | ~91–94% | CoStar / RealPage / rent roll |

*Some fields disagree across vendors (year built, class, lease-up path); differences
are preserved rather than reconciled away and are examined in the analysis.*

---

## Repository layout

```
data/                          Raw source files (as provided — do not edit)
  market/                      CoStar + RealPage 5-mile market & comp exports
    CoStar_5mi_Property_List.xlsx          67-property roster w/ unit mix, rents, geo
    CoStar_5mi_Overall_Analytics.xlsx      submarket quarterly time series (2000–2026)
    CoStar_5mi_Property_Analytics.xlsx     per-property quarterly series (67 props)
    RealPage_5mi_Property_List.xlsx        24-property roster w/ sales/loan/occ/rent
    RealPage_Provo_Historical_Rent_and_Occ.xlsx  67-property quarterly rent/occ history
  hellodata/
    HelloData_5mi_Unit_Details_2026-07-13.csv  unit-level leases/listings, 34 props
  financials/                  Subject-property operations
    Operating_Statement_RedIQ_thru_2026-05.xlsx  RedIQ export (Overview + coded detail)
    Trailing_PL_Detail_2026-05-31.xlsx     native operator T12 (Neighborly)
    Rent_Roll_2026-06-16.xlsx              current rent roll
    Aged_Receivables_2026-05-31.xlsx       delinquency / AR aging
    Rentable_Items_Detail_2026-06-16.xlsx  parking/carport/storage inventory
  tax/
    2025_Tax_Bill/             15 parcel PDFs (paid 2025 tax)
    2026_Assessed_Value/       15 parcel PDFs (2026 assessed value + value history)

analysis/                      Our work product
  rr-t12-intake/               Underwriting intake (RR-T12 processor output)
  rent-comps/                  Rent Comps – High Level deliverable
  supply-chart/                5-mile Supply & Absorption chart
  tax/                         Real-estate tax analysis
  notes/                       Cross-workstream synthesis notes

.claude/skills/                Analysis tooling (packaged skills)
  rr-t12-processor/            Operating-statement + rent-roll standardization/audit
  rent-comps-high-level/       Rent-comp workbook + map + preview
  supply-chart/                Competitive-supply reconciliation + forecast
```

## Source file inventory

| File | What it is | Feeds |
|---|---|---|
| CoStar 5mi Property List | Competitive roster, unit mix, asking rents, lat/long | supply-chart, rent-comps |
| CoStar 5mi Overall Analytics | Submarket quarterly inventory/rent/occ/absorption/deliveries | supply-chart |
| CoStar 5mi Property Analytics | Per-building quarterly series incl. deliveries | supply-chart |
| RealPage 5mi Property List | Roster w/ sales comps, loan terms, occ, effective rent | supply-chart |
| RealPage Provo Historical | 67-property quarterly effective/asking rent + occupancy | market context |
| HelloData Unit Details | Unit-level executed leases + listings, 34 properties | all three skills |
| Operating Statement (RedIQ) | Standardized coded T12 (Jun-25→May-26) | rr-t12 (audit mode) |
| Trailing P&L Detail | Native operator monthly actuals | rr-t12 (NOI cross-tie) |
| Rent Roll (2026-06-16) | Current unit-level rent roll | rr-t12, rent-comps |
| Aged Receivables | AR aging / delinquency | financial diligence |
| Rentable Items Detail | Parking/carport/storage units | rr-t12 (other income) |
| 2025 Tax Bill (15 PDFs) | Paid property tax by parcel | tax analysis |
| 2026 Assessed Value (15 PDFs) | Assessed value + 2022–2026 value history | tax analysis |

---

## Analysis outputs (2026-07-13)

Start with **`analysis/notes/Cross_Workstream_Review.md`** — it ties the four workstreams
into one underwriting picture and cross-checks every shared figure.

| Workstream | Location | Headline |
|---|---|---|
| **Underwriting intake** (RR-T12, audit mode) | `analysis/rr-t12-intake/` | Standardized in-place **NOI $3.01M** (62% margin), occ 93.75%. Operator's printed NOI ($3.36M) overstates true NOI ~$353k by booking taxes+insurance below its NOI line. HD T90 market rent $1,595 / eff $1,501. |
| **Rent comps – high level** | `analysis/rent-comps/` | Subject **~4% under** comp rent/unit ($1,595 vs $1,660), at par on $/SF. Mark-to-market concentrated in **2BR (−5.2%, 55% of units)** and 3BR. Workbook + satellite map + preview. |
| **Supply chart** | `analysis/supply-chart/` | 7,632-unit 5-mi inventory; **zero forward pipeline**; re-stabilizes to **95% occ by Y1** under base demand. Workbook + map. |
| **Real-estate tax** | `analysis/tax/` | In-place **$302,467/yr** ($1,260/unit); reassessment-on-sale → **~$350k at $300k/unit**. Reconciles the RedIQ tax line to the penny. |

**Underwriting bottom line (from the review):** standardized in-place NOI ≈ **$3.01M**; adding
the omitted commercial parcel trims true in-place NOI to ≈ **$3.00M**; the Utah tax reset on
sale (~$300k/unit basis) yields a **Year-1 reassessed NOI ≈ $2.95M** before rent growth — with
loss-to-lease + mark-to-market upside supported by a market that has **no forward supply**.

**Blocking items before underwriting** (see the review for the full list): model the tax reset
to purchase price (+ add parcel 001); underwrite Other Income/RUBS to the **T12**, not the rent
roll (the roll omits ~$329k/yr of RUBS); carry the standardized **$3.01M NOI**, not the operator's
$3.36M; and **confirm the auto-selected rent-comp set** (consider adding The Yard, Solhavn).

## Analysis tooling note

The `rr-t12-processor` skill's parser was extended during this run to read the operator's
**ResMan/Neighborly** rent-roll and T12 export layout (the initial run parsed 0 units). Those
fixes live in `.claude/skills/rr-t12-processor/scripts/` and are committed with the deliverable.

---

*Deal folder initialized 2026-07-13. Analysis run 2026-07-13.*
