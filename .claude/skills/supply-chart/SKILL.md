---
name: supply-chart
description: >-
  Build a 5-mile new-construction "Supply Chart" for a multifamily underwriting
  deal. Reconciles CoStar and RealPage 5-mile exports into one competitive-
  supply roster, buckets each property by lifecycle stage, and writes a
  workbook with a relative-year (TTM) Supply & Absorption forecast — supply,
  absorption, and occupancy with editable demand scenarios and pipeline
  toggles. Subject rent/occupancy rows come straight from a HelloData Unit
  Details CSV (mix-weighted, like the model's Cash Flow Annual tab) — no
  intake workbook needed. HelloData also drives comp lease-up occupancy and
  mix-weighted comp rents; Y0 supply is live-linked to the roster and ties to
  CoStar's deliveries series. Also exports a companion map. Use when asked to
  build, update, or automate a supply chart / competitive supply or rent
  analysis, or given CoStar + RealPage radius exports for a deal.
---

# Supply Chart

## What this produces
A single `build_supply_chart.py` run writes **two deliverables by default**:

**A. The Supply-Chart workbook** (mirroring `reference/EXAMPLE_Seasons_Supply_Chart_v2.xlsx`):

1. **Competitive Analysis** — the new-construction roster grouped into four
   lifecycle (colour-coded) buckets.
2. **Supply & Absorption** — the relative-year (TTM) supply / absorption /
   occupancy forecast, subject rent & occupancy rows, the 3rd-party-forecast
   block, demand & rent-growth scenarios, and the editable pipeline blocks
   (see §4). Editable inputs use the model's blue-font convention.
3. **Reconciliation Log** — every property with its merged values, sources, and
   any conflict notes, so the analyst can audit the automated decisions.
4. **Diligence** (only with `--diligence`) — researched pipeline + shadow supply.

**B. The companion HTML map** — `<subject>__Map.html`: a single branded,
self-contained interactive map (Leaflet bundled inline — no CDN, no image
dependencies), plotting the subject + roster on a satellite basemap, colour-coded
by the same buckets, with numbered pins that match the chart's rows, a 5-mile
ring, and per-property popups. Skipped only with `--no-map`. **These two — the
workbook and the HTML map — are the entire deliverable.** (No PNG or other image
is produced.)

This supply layer is the input to the **rent-analysis** step: it sits on top of
the historical overall occupancy / absorption / deliveries series (CoStar Data
Analytics) so demand can be forecast and the "when is occupancy strong enough to
push rents" question answered. (Rent analysis is a *separate, later* step — this
skill only builds the supply chart.)

## Operating procedure (the order to work in)
1. **Build the supply chart standalone first** — reconcile the exports, bucket the
   roster, build the Supply & Absorption forecast. Hand it over as its own workbook.
2. **Let the user refine** — delivery quarters, demand scenarios, source selection,
   diligence corrections. Re-run with their edits.
3. **Make it jive with every input you were given** before calling it done:
   - the **RR-T12 intake workbook** (if supplied via `--intake`) drives the
     subject market/effective-rent and occupancy rows — confirm those reconcile;
   - the delivered roster ties to CoStar's deliveries series (the completeness
     check, §3a);
   - diligence corrections (if run) are reflected in the buckets and pipeline.
4. **Only then ask whether to incorporate into the underwriting model.** The
   subject rows already carry the model links by default (they sit dormant as
   clean blanks until the tab is in the model), so incorporating is just the
   carry-over: the user drags the tabs in, or you embed them with
   `scripts/embed_into_model.py` — see **Incorporating into the underwriting
   model** below.

## Inputs (5-mile radius around the subject)
Three required exports, plus two strongly-recommended companions:

| Input | Provides | Notes |
|---|---|---|
| **CoStar 50-unit property roster** (`Export…xlsx`) | Property-level roster of existing assets: name, address, year built, **construction begin**, units, bed mix, stories, owner. | Used as the **primary roster + unit counts + delivery timing basis**. Misses sub-50-unit and not-yet-tracked pipeline deals. |
| **CoStar Data Analytics — OVERALL** (`MultifamilyDataGrid`) | Quarterly submarket time series: inventory, rent, occupancy, absorption, under-construction, **deliveries by quarter**. | Source of **Total Current Inventory** and the historical TTM actuals. A trailing "QTD" row (partial quarter) is detected and never used as a TTM anchor. |
| **RealPage 5-mile** | Competitor roster with **per-property occupancy & effective rent**, plus the **forward pipeline** (`Property Status` = Pre-Planned / Under Construction). | Catches deals CoStar hasn't picked up (sub-50u, pipeline). Both the classic roster export and the newer **Grid Performance** shape (Name + performance columns only) are parsed. |
| **CoStar Data Analytics — PER-PROPERTY** (`--costar-property-analytics`) | One quarterly series **per building**: rent, occupancy, and each building's own **`Deliveries Units`** event. | **The authoritative delivery-quarter source.** With it, every comp's quarter is pinned exactly and the roster's TTM delivered units **tie to the overall deliveries series to the unit**. Also fills comp-occupancy gaps, gives lease-up trajectories, and doubles as the subject rent history (`--costar-subject-rents` defaults to it, same format). |
| **HelloData 5-mile "Unit Details" CSV** (`--hellodata`) | Unit-level executed leases + active listings for the subject **and** every covered comp. | Drives the **subject rows** (mix-weighted rents — no intake workbook needed) and, for covered comps, the **mix-weighted roster rents** and the **lease-up occupancy / leasing-pace read** (see below). A subject-only pull works too. |

> **CoStar rent/occupancy:** if the CoStar export includes `Avg Asking/Unit` and
> `Vacancy %` (the "v2" pull), the script reads them and **cross-checks against
> RealPage** — occupancy gaps ≥2 pts and rent gaps ≥5% are flagged in Notes, and
> both sources sit side-by-side in the Reconciliation Log. Note CoStar rent is
> *asking* and RealPage rent is *effective*, so a gap is expected. Choose which
> source drives the chart with `--occ-source` / `--rent-source` (default CoStar).
> If the CoStar export lacks those columns ("v1"), occupancy/rent fall back to
> RealPage automatically.

## How to run
```bash
python scripts/build_supply_chart.py \
  --subject-name    "The Sarah at Lake Houston" \
  --costar-roster   path/to/CoStar_5mi_Properties_List.xlsx \
  --costar-analytics path/to/CoStar_5mi_Overall_Analytics.xlsx \
  --costar-property-analytics path/to/CoStar_5mi_Properties_Analytics.xlsx \
  --realpage        path/to/Realpage_5mi_Properties.xlsx \
  --hellodata       path/to/HelloData_5mi.csv \
  --out             output/<Deal>__Supply_Chart.xlsx
```
Optional flags:
- `--as-of "2026 Q2"` — analysis quarter = the quarter Y0 ends at (defaults to the **latest COMPLETE quarter** in the analytics file — a partial "QTD" row is never used as the anchor; forcing a QTD quarter annualizes the partial window, labeled)
- `--close "2026 Q4"` — close quarter (Y1 start); default as-of + 2 quarters; editable in the workbook, and the Y1–Y6 window labels re-derive from it live
- `--target 0.95` — stabilization occupancy goal
- `--occ-source costar|realpage`, `--rent-source costar|realpage` — which source drives the chart (default `costar`); HelloData mix-weighted rent wins wherever it covers a comp
- `--pipeline-dates path.csv` — analyst-supplied delivery quarters for pipeline deals (see below)
- `--costar-property-analytics path.xlsx` — the CoStar **per-property** analytics export; makes delivery pinning authoritative (TTM windows then tie to CoStar's series exactly), fills occupancy gaps, and doubles as the subject rent history
- `--intake path.xlsx` — a pre-built RR-T12 underwriting intake; adds **subject rows** (market/effective rent from HelloData mix-weighted, occupancy from the T12 financials) to the Supply & Absorption tab
- `--hellodata path.csv` [`--t12 path.xlsx`] — **the independent alternative to `--intake`** (no intake workbook, no rr-t12-processor). Accepts the subject-only HelloData "Unit Details" CSV **or the 5-mile multi-property export** (the subject's rows are filtered out by name). The skill computes the subject rows exactly the way the model's **Cash Flow (Annual)** tab does: each floor plan's executed rents averaged per month, **mix-weighted by the plan's unit count**, then TTM-averaged into the relative-year windows; occupancy comes from the **T-12** (`1 − vacancy/AGPR`) when supplied, else the subject's own CoStar/RealPage per-property occupancy. (`scripts/subject_intake.py`.)
- `--costar-subject-rents path.xlsx` and/or `--realpage-subject-rents path.xlsx` — per-property rent histories used to extend the subject rents before HelloData coverage; whichever tracks HelloData more closely in the overlap is auto-selected (varies by market)
- `--latlng path.csv` — analyst-supplied `property,latitude,longitude` for comps CoStar doesn't geolocate (RealPage-only pipeline deals). Needed to build the map when the CoStar export doesn't carry a coordinate for every comp — the run emits a `…__map_latlng_TEMPLATE.csv` listing exactly which comps to fill (see **Positioning & the map** below)
- `--subject-latlng "lat,lng"` — pin the subject anchor exactly. Normally the subject's own CoStar-roster coordinate is used automatically; pass this only if the roster lacks it
- `--no-model-link` — by **default** the subject rows are wired to the underwriting model (see **Incorporating into the underwriting model** below) so the tab is carry-over-ready; pass this for a pure standalone chart with no model references. `--model-sheet "…"` overrides the target tab (default `Cash Flow (Annual)`)
- `--no-map` — skip the companion HTML map (it is produced by **default**)

The script prints a reconciliation report to the console and writes exactly **two
deliverables: the workbook and the HTML map** (`<subject>__Supply_Chart.xlsx` +
`<subject>__Map.html`) — nothing else. Always read the console report and the
**Reconciliation Log** sheet, then review the workbook before handing it off.

### Dating the pipeline
Under-construction deals are auto-dated (from CoStar `Construction Begin` + ~24
mo) and flow into the forecast automatically. Proposed deals without a date are
listed but undated; every run writes `<out>__pipeline_dates_TEMPLATE.csv` of the
undated deals. Fill `est_delivery` (`Q2 2028`) and re-run with `--pipeline-dates
that.csv`, or just edit the delivery quarter directly in the **Proposed Pipeline**
block on the Supply & Absorption tab. Whether a proposed deal adds supply is
controlled by its **Built In** toggle (Bear only / Bear+Base / All / None).

### Companion HTML map (produced by default)
The main run writes a single **self-contained HTML map** alongside the chart — a
branded Leaflet map (Leaflet bundled inline from `assets/vendor/`, **no CDN and no
image/PNG output**). It plots the subject + competitive roster on a **satellite**
basemap, colour-coded by the same lifecycle buckets, with **numbered pins that
match the chart's rows**, a gold 5-mile ring, a high-contrast magenta subject
star, per-property popups, and a legend. To regenerate the map alone (or add
`--diligence` shadow pins), run `scripts/build_map.py` directly:
```bash
python scripts/build_map.py \
  --subject-name "Aura Beacon Island" \
  --subject-address "2200 Beacon Cir, League City, TX 77573" \
  --costar-roster examples/aura_beacon_island/CoStar_5mi_50unit_properties.xlsx \
  --costar-analytics examples/aura_beacon_island/CoStar_5mi_Data_Analytics.xlsx \
  --realpage examples/aura_beacon_island/Realpage_5mi.xlsx \
  --out output/Aura_Beacon_Island__Map.html
```
Positions come from **exact lat/lon only** (CoStar's export + any `--latlng` CSV) —
the map is **never geocoded**, and it is only built once every comp has a real
coordinate (see **Proximity & positioning** below). The only Python dep is
`openpyxl`; the map needs network for basemap tiles at view time.

## Methodology

### 1. Reconcile the two rosters
- Match properties across CoStar and RealPage by **street address** (leading
  number + first significant street word; handles ranges and directionals), with
  a **name fallback** for missing/typo'd addresses.
- **Unit counts:** keep CoStar's; flag a note when the two sources differ by ≥3
  units (±2 is treated as noise).
- **Occupancy:** both sources kept side-by-side; the displayed value follows
  `--occ-source` (default CoStar); a ≥2-pt gap is flagged in Notes.
- **Rent:** the roster's **Avg Mkt Rent** is an **asking/market** figure. Where
  the HelloData 5-mi CSV covers a comp, its **mix-weighted trailing-90-day
  asking rent** is the displayed figure (highest fidelity; divergence vs CoStar
  ≥5% is noted, and the HD ask/eff sit in the Reconciliation Log). Otherwise
  CoStar asking is the source (`--rent-source costar`, default). RealPage
  exports only *effective* rent, which is **never** shown in this column — it
  contributes only if a given pull also carries an asking column
  (`--rent-source realpage`, else CoStar), and `average` blends the available
  asking values. CoStar-asking-vs-RealPage-effective gaps (≥5%) are still
  surfaced in Notes/Reconciliation Log.
- **Status:** a forward-looking status (Pre-Planned / Under Construction) from
  either source wins, so pipeline deals are never mislabeled as existing.
- The **subject property** is dropped from the competitive roster.

### 2. Pin the delivery quarter (the key cross-comparison)
Neither roster gives a delivery *quarter* (only a year). For **delivered**
properties the quarter comes from, in priority order:

0. **The CoStar per-property analytics** (`--costar-property-analytics`, or the
   same-format `--costar-subject-rents` file): each building's own `Deliveries
   Units` event is the **authoritative** quarter — pins from it make the
   roster's TTM delivered units tie to the overall deliveries series exactly.
   **Always ask for / use this export when available.**
1. An exact unit-count match against the overall deliveries series within ±1
   year pins the quarter precisely (e.g. Timbers 274u → Q2 2023);
2. otherwise the same-year quarter with the closest delivered count is used and
   flagged *"Delivery quarter estimated"* (keeps the absorption table populated
   in large markets — but in a heavy-supply market two same-year comps can
   easily land on the wrong quarters, which is exactly what the per-property
   file fixes);
3. if the year has no recorded deliveries, only the year is kept (`Q? <year>`).

**Under-construction** deals are auto-estimated from CoStar's `Construction
Begin` + ~24 months (reconciled against CoStar's completion year) and pushed
into the future so they enter the forecast; **proposed** deals with no date get
`TBD` for the analyst. A delivered comp only RealPage tracks (CoStar never
counted it) is kept — it's real supply — and noted *"RealPage-only — not in
CoStar's 5-mi series"* so the tie-out stays explainable.

### 3. Bucket each property (status-driven)
Buckets are driven by the lifecycle status from **both** sources, with precedence
*delivered → under-construction → proposed* (an "it exists" signal from either
source beats a stale "pre-planned"):
- **STABILIZED / STABILIZING** — delivered and ≥90% occupied (or an older,
  within-lookback asset that simply underperforms).
- **LEASING UP** — delivered within ~2 years and below 90% occupied. When the
  HelloData 5-mile CSV covers the property, the verification happens
  automatically: displayed occupancy = **HD cumulative lease-up occupancy**
  (distinct units ever leased, less units back on market, over total units —
  vendor occupancy is often stale on lease-ups) and the Notes carry the
  **leasing pace** (`HD (90d): occ ~54%, ~22 leases/mo`). Without HD coverage
  the row keeps the **"Verify rent/occ w/ HelloData"** flag.
- **UNDER CONSTRUCTION** — ground has broken: a UC status from either source, **or
  `Construction Begin` ≤ the as-of quarter** (even if a source still lags as
  "Proposed").
- **PROPOSED** — not yet started: `Construction Begin` in the future (or absent)
  and a proposed/pre-planned status. A future begin still yields an *estimated
  completion* (begin + ~24 mo) for the pipeline, but the deal stays Proposed
  until ground breaks.

Only genuine new supply is charted: deliveries within the last
`NEW_CONSTRUCTION_LOOKBACK_YEARS` (default 4) plus the entire pipeline. Each
section is colour-coded, carried over from the reference template: **blue**
(stabilized), **orange** (leasing up), **green** (under construction), **red**
(proposed), each with a light matching row tint.

### 3a. Completeness check — tie the roster to CoStar's deliveries series
The tie-out is now **built in**: every run prints a per-TTM-window
reconciliation to the console AND writes the same lines into the collapsed
DETAIL block on the Supply & Absorption tab. For each window it compares
**roster (CoStar-tracked) + subject add-back** against CoStar's `deliveries`
series, reporting any **RealPage-only supply** separately (real units CoStar's
series misses — kept on the roster, never counted against the tie). The
components of a residual:
- **The subject itself.** CoStar's *submarket* deliveries include the subject,
  but the subject is dropped from the *competitive* roster — the script adds
  its units back automatically (from the per-property analytics delivery
  event). (Worked example: Aura -Y3 = 906 = roster 616 **+ subject Aura 290** —
  exact.)
- **Sub-50-unit product** CoStar's submarket series counts but the 50-unit
  property pull never lists (small, can't be itemized — reported as residual).
- **A genuinely missing or mis-dated 50+ comp** — the case worth catching, and
  flagged (`roster over by N — check pins`). With the per-property analytics
  supplied the pins are authoritative and every window should tie **to the
  unit**; without it, look for a comp pinned to the wrong quarter or dropped
  for an off-by-one year.

Read the console tie-out on every run. If a window is flagged, fix it before
handing over — the Y0 New Supply cell on the chart reads the roster live, so a
bad pin flows straight into the headline figure.

### 4. Supply & absorption forecast (the "Supply & Absorption" tab)
The rent-analysis core: a market-level view of **new supply, absorption, and
overall occupancy** in **relative-year (trailing-12-month) columns**, built from
the CoStar Data Analytics series + the supply pipeline, on **live Excel formulas**.

- **Columns** are TTM windows anchored to the as-of quarter: **Y0** = the T12
  ending at as-of, **-Y1…-Y6** step back a year each (toward 2020); **Y1…Y6** are
  the hold years anchored to an editable **Close Quarter** (default as-of + 2
  quarters), so the analysis→close gap is one cell.
- **As-of vs Close, spelled out on the tab** (gray notes beside each input):
  **As-of Quarter** = where Y0 ends — defaults to the latest **complete** CoStar
  quarter (a "QTD" row is never the anchor). **Close Quarter** = expected deal
  close = the start of Y1; pipeline deliveries bucket into hold years off this
  anchor, and the **Y1–Y6 period labels are live formulas** — edit Close and the
  windows (and which hold year each delivery lands in) shift with it.
- **Historical years** = CoStar 5-mi actuals (Σ deliveries, Σ absorption,
  end-of-window occupancy). A window with **fewer than 4 complete quarters** of
  data shows its absorption **annualized** (×4/n), labeled `(3q ann.)` in the
  period row and footnoted in the DETAIL block — a 3-quarter total shown as a
  year is misleading.
- **Y0 is LINKED, not typed**: `New Supply (Y0)` = live `SUMIFS` over the
  Competitive Analysis roster's units by delivery quarter (hidden helper col
  parses each row's Est. Delivery), plus the subject's units if it delivered
  in-window; `inventory = -Y1 inventory + Y0 supply`; `occupied = -Y1 occupied +
  Y0 absorption`; `occupancy = occupied / inventory`. Re-date a delivery on the
  roster (or edit Y0 absorption) and supply **and** occupancy move together.
  The DETAIL block carries the audit: Y0 roster-vs-CoStar tie (should be exact
  with per-property analytics), with RealPage-only supply broken out.
- **Forecast years**: `Inventory += scheduled pipeline`; `Occupied += selected
  annual demand` (capped at target × inventory); `Occupancy = Occupied /
  Inventory`. Plus a **cumulative-unabsorbed** row since -Y3.
- **Pipeline = two blocks** (right side): **UNDER CONSTRUCTION** is linked from
  the Competitive Analysis roster and counts in every scenario; **PROPOSED** is
  speculative with a per-deal **"Built In"** dropdown (*Bear only / Bear+Base /
  All / None*) so a deal layers into the downside (more-supply) case only. Each
  hold-year's new supply = UC + proposed built under the selected scenario.
- **Subject rows**: market & effective rent, occupancy, and **concession %**, plus
  **YoY %** rows. A collapsed ("+") detail group lists the source used per year
  (HelloData vs CoStar) and the UC-vs-CoStar reconciliation. Forward concession %
  is an editable assumption block.
- **3rd-party forecast block** (model-linked): a compact table comparing
  **TMG's own market-rent growth** (the focus — gold row, = the subject's
  market-rent YoY) against **CoStar / RealPage / Yardi / GreenStreet** forecasts
  and their **consensus**, with a per-row AVG column. Sources link to the model's
  `Rent & Occ Data` rows 31–34 (resolve when the tab is in the model). The point
  is to read OUR growth against the supply recovery above (primary) and the
  external consensus (secondary). Distinct from the model's AGPR growth — this is
  a pure asking-rent trend.
- **Scenario inputs are collapsed** under a single summary header (click **+** to
  expand): the **Implied 5-mi Occupancy** block (Bear/Base/Bull), the editable
  **market-rent-growth / concession** blocks, and the derived **effective-rent-
  growth** block. Keeps the tab focused on the supply/occupancy story and the
  TMG-vs-forecast comparison; the scenario machinery is one click away.
- **Demand** is a Bear/Base/Bull annual-absorption assumption (Base = trailing
  CoStar average).
- **Editable inputs** follow the model's convention — **blue font on a light
  fill** (stabilization target, close quarter, demand scenario & the three
  absorption levels, each proposed deal's delivery quarter & Built-In, and the
  rent-growth/concession assumptions). Section headers use the model's navy
  (`FF153D64`); the formatting is kept consistent with the TMG model throughout.
- A **reconciliation note** compares the scheduled pipeline (Include=Y) against
  CoStar's current Under-Construction unit count so the pipeline ties out.

Reading the occupancy row shows **when the market re-stabilizes** to target — i.e.
when occupancy is strong enough to push rents.

**Subject rows** (with `--intake`, or the independent `--hellodata`/`--t12`): the
tab also shows the subject's own **market rent, effective rent, and occupancy** in
the same relative-year columns.
Source hierarchy: **HelloData mix-weighted** rents where available (≈2023→);
before that, **CoStar or RealPage per-property** rents — whichever tracks
HelloData more closely in the overlap is auto-selected (CoStar tends to win in
some markets, RealPage in others), level-aligned to HelloData via the overlap
ratio. The chosen source is shown in the row label (`…→HD`) and per-year in the
collapsed detail group. Subject occupancy comes from the **operating statements /
T12** as far back as they reach, then falls back to **CoStar** per-property
occupancy, then **RealPage's** (when its per-property export carries an occupancy
metric). Forecast-year
subject rents are deferred to the (later) market-rent-growth → effective step —
unless the chart is linked to the model (next section), in which case Y0→Y6 read
the model's own projection.

## Incorporating into the underwriting model
The subject **Market Rent**, **Effective Rent**, and **Occupancy** rows (cols
Y0→Y6) are written **by default** as `IFERROR`'d **internal references** to the
TMG model's `Cash Flow (Annual)` tab, so every chart is carry-over-ready: drag
the tabs into the model and they resolve to the deal's own projected path next
to the 5-mile market frame, as a **sanity overlay** (the chart reads the model;
it does *not* drive it). Until the tab is in the model the refs show a clean
blank (Y1→Y6) or the chart's own value (Y0 fallback), not `#REF!`. The YoY% and
Concession% rows are live formulas across all columns, so once carried over they
show the **model's** market-rent growth, effective-rent growth, and concession
trend in the same frame — the comparison is implicit, no separate delta block.
The fixed mapping:

| Subject row | Model row (`Cash Flow (Annual)`) | Y0 = col I | Y1–Y6 = cols J:O |
|---|---|---|---|
| Market Rent | row 4 (Market Rent /U) | ← `F` | ← `K,L,M,N,O,P` |
| Effective Rent | row 5 (Eff Mkt Rent /U) | ← `F` | ← `K:P` |
| Occupancy | row 14 (Physical Occupancy) | ← `F` | ← `K:P` |

Historical columns (−Y6…−Y1) stay as the static RealPage/HelloData actuals.

**Two delivery modes** (both use the same default linked tabs):
- **User drags the tabs in** (the default expectation) — they Move/Copy the
  `Supply & Absorption` (and its `Competitive Analysis` dependency) sheets into
  the model; the internal refs resolve to the model's own `Cash Flow (Annual)`.
  Until then the standalone shows clean blanks / Y0 fallbacks (IFERROR), not
  `#REF!`.
- **You embed it for them** — `scripts/embed_into_model.py` grafts the chart's
  sheets into the model **at the package/XML level**, so VBA, charts, conditional
  formatting, pivot caches, and external links are preserved byte-for-byte (it
  never round-trips the .xlsm through openpyxl, which silently drops those — it
  warns on this very model). It only edits `styles.xml` (appending + index-
  remapping the chart's styles), `workbook.xml`, the rels, and `[Content_Types]`,
  drops `calcChain.xml`, and sets `fullCalcOnLoad` so the links compute on open:
  ```bash
  python scripts/build_supply_chart.py … --out chart.xlsx     # links are default
  python scripts/embed_into_model.py \
    --chart chart.xlsx --model "TMG Acquisition Model.xlsm" \
    --out "TMG Acquisition Model__with_Supply_Chart.xlsm"
  ```
  It self-validates (zip integrity, XML well-formedness, every retained model
  part byte-identical) and prints what changed. Always open the result in Excel
  once to confirm before relying on it.

Keep the distinction the model already encodes: the chart's **market-rent
growth** is a pure asking-rent trend; the model's **AGPR growth** bakes in
loss-to-lease/gain-to-lease burn-off and lease-term roll. They are *not* the same
line — compare market-rent growth to the model's `RRA` GPR-growth row, not AGPR.

## Research & diligence (opt-in)
The mechanical build trusts whatever CoStar/RealPage report. When the user asks to
**research the pipeline / verify the supply / do diligence** (or runs with
`--diligence`), perform this phase — it is not run by default.

Every build emits `…__diligence_TEMPLATE.csv` (cols: `type,property,units,
est_delivery,status,leasing_pace,notes,source` — plus an optional `address`
column you can add). The research workflow:

1. **Per-project diligence (Part A).** For each lease-up / UC / proposed deal,
   web-research the **actual site / development plans** (city planning portal,
   Community Impact / local press, developer pages) and confirm: construction
   status, expected delivery quarter, developer/owner, unit count, any
   **affordable or age-restricted** component, leasing pace, and the **street
   address**. **Cite a source URL.** What each filled field does on re-run
   (`type=pipeline`, matched by name):
   - **`est_delivery` / `units`** — re-pin the quarter and unit count; flow into
     the buckets and absorption forecast.
   - **`status`** — reclassifies (`under construction`/`leasing` → UC). Statuses
     that **remove a deal from the competitive set** (still shown on the Diligence
     sheet, so it's documented, not silent): *cancelled / withdrawn / dead*, *not
     multifamily* (a church conversion or for-sale homes), or an explicit analyst
     *exclude* / *different / out-of submarket*. Use these — a dead deal or an
     out-of-submarket comp that doesn't belong wrecks the count and the tie-out.
     The drop is keyed **only off the `status` field**, never the free-text
     `notes` — so a note can safely say "…excluded below" or "distinct from the
     out-of-submarket comp" without accidentally dropping a valid pin.
   - **`address`** (optional column) — a researched street address for the
     Diligence sheet's record. (Map/Proximity positions come from exact lat/lon via
     `--latlng`, not from the address — the skill never geocodes.)
2. **Shadow-supply scan (Part B).** Research the 5-mile radius for **latent supply
   not in the vendor data**: multifamily **rezonings**, **entitled / under-contract**
   apartment land, large vacant MF-zoned tracts, master-planned MF phases, and
   newly announced developments. Add each as a `type=shadow` row with a source.
   *Optional companion:* if the separate **`land-use-analysis`** skill is available,
   it automates the data-driven half of this scan — it pulls county parcels +
   municipal zoning and ranks genuinely-developable vacant MF-zoned land near the
   subject, which feeds straight into these `type=shadow` rows. It is **entirely
   optional**; this skill is self-contained and never depends on it — Part B can be
   done by hand exactly as above.
3. Be skeptical — if a project can't be verified, say so in `notes` rather than
   guessing. Then re-run with `--diligence filled.csv`: the workbook gains a
   **Diligence** sheet (pipeline diligence + shadow-supply watch list) and the
   researched delivery dates flow into the forecast. The `type=shadow` rows are
   also plotted on the map.

**Tie-out tip:** if the bundle includes a CoStar **per-property** analytics file
(per-building `Deliveries` by quarter), pass it as
`--costar-property-analytics` — pinning is then automatic and authoritative and
the historical TTM windows reconcile to CoStar's overall series exactly
(subject added back automatically; see §3a). No manual `est_delivery` rows
needed for delivered comps.

## Proximity & positioning
**Positions come from exact lat/lon only — the skill never geocodes.** This is
deliberate: geocoding proposed/intersection-only deals produced pins that were
miles off. Coordinates come from two sources:

1. **CoStar's exported `Latitude`/`Longitude`** (newer Property List exports carry
   them). Used directly for the **Proximity (mi)** column and the map for every
   CoStar-listed comp **and the subject** (its own roster coordinate anchors the
   map — no `--subject-latlng` needed). Because the CoStar 5-mile export is a true
   radius, these are all in-radius.
2. **Analyst-supplied `--latlng` CSV** for the RealPage-only pipeline deals CoStar
   doesn't place.

**The 5-mile radius is enforced.** Any comp whose exact distance exceeds 5 mi is
**dropped** from both the chart and the map (logged to the console). CoStar comps
are always in-radius, so this only removes RealPage-only edge deals.

**Coordinate-gated map workflow.** If any competitive comp lacks a coordinate, the
run writes the **chart**, **holds the map**, and emits a
`…__map_latlng_TEMPLATE.csv` listing the missing comps with their addresses. Fill
the `latitude`/`longitude` (a combined `"lat, lng"` pasted in the latitude cell is
also accepted) and re-run with `--latlng that.csv`; the map builds once every comp
has an exact point. So the standing pattern is: **run → chart + a request for any
missing coordinates → supply them → exact HTML map.** A comp with no coordinate
stays in the chart (its Proximity is left blank) but is not plotted.

## Analyst follow-ups the script intentionally leaves open
- **Lease-up rent & occupancy** — automatic for comps the HelloData 5-mi CSV
  covers (mix-weighted rents + cumulative lease-up occupancy + pace); any
  lease-up NOT covered keeps the "Verify rent/occ w/ HelloData" flag for a
  manual pull.
- **Pipeline timing** — undated Pre-Planned deals (`TBD`) are listed but not in the forecast; fill the emitted `…__pipeline_dates_TEMPLATE.csv` and re-run with `--pipeline-dates`, or research them via the diligence phase above.

## Tunable thresholds
Top of `scripts/build_supply_chart.py`: `DEFAULT_STABILIZATION_TARGET`,
`STABILIZED_OCC`, `NEW_CONSTRUCTION_LOOKBACK_YEARS`, `CONSTRUCTION_MONTHS`.

## Worked examples
`examples/sarah_lake_houston/` — the **full recommended bundle** (Houston):
overall + per-property CoStar analytics, RealPage roster, the HelloData 5-mile
CSV, and a metro-wide RealPage historical-performance file. Runs with **no
intake workbook** and every TTM window ties to CoStar's deliveries to the unit
(Y0 = 813 CoStar-tracked + 105 RealPage-only), with HD-driven lease-up
occupancy (e.g. The Clayton: vendor said 2%, HD cumulative lease-up says ~54%
at ~22 leases/mo):
```bash
python scripts/build_supply_chart.py \
  --subject-name "The Sarah at Lake Houston" \
  --costar-roster    examples/sarah_lake_houston/CoStar_5mi_Properties_List.xlsx \
  --costar-analytics examples/sarah_lake_houston/CoStar_5mi_Overall_Analytics.xlsx \
  --costar-property-analytics examples/sarah_lake_houston/CoStar_5mi_Properties_Analytics.xlsx \
  --realpage         examples/sarah_lake_houston/Realpage_5mi_Properties.xlsx \
  --hellodata        examples/sarah_lake_houston/HelloData_5mi.csv \
  --realpage-subject-rents examples/sarah_lake_houston/Realpage_Houston_Historical_Performance.xlsx \
  --out output/The_Sarah_at_Lake_Houston__Supply_Chart.xlsx
```

`examples/bella_mirage/` — a large, supply-heavy Phoenix market (104 comps,
26.6k-unit inventory) that exercises all four buckets and the subject rows. Run:
```bash
python scripts/build_supply_chart.py \
  --subject-name "Bella Mirage" --subject-address "3800 N El Mirage Rd" \
  --costar-roster    examples/bella_mirage/CoStar_5mi_50unit_properties.xlsx \
  --costar-analytics examples/bella_mirage/CoStar_5mi_Data_Analytics.xlsx \
  --realpage         examples/bella_mirage/Realpage_5mi.xlsx \
  --intake           examples/bella_mirage/Bella_Underwriting_Intake.xlsx \
  --costar-subject-rents examples/bella_mirage/CoStar_5mi_property_rents.xlsx \
  --out output/Bella_Mirage__Supply_Chart.xlsx
```

`examples/canyon_ridge/` holds the real exports for Canyon Ridge (Boise, ID),
including the CoStar v2 pull (with rent/occ) and a sample `pipeline_dates.csv`.
Running the command above reproduces `output/Canyon_Ridge__Supply_Chart.xlsx`:
3 stabilized comps (445 u, ≈fully absorbed near-term) plus a 1,763-unit proposed
pipeline. With the pipeline dated via `--pipeline-dates`, the deliveries spread
across 2026–2028 and "% to be absorbed" rises to ≈28% — the forward supply the
deal will compete with.
