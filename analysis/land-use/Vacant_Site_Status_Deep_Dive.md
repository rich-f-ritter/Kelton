# Vacant-Site Status — Deep Dive (The Kelton)

**Purpose:** pin down the *actual* status and development intent of the vacant sites flagged in the
land-use analysis, using American Fork & Lehi **General Plan (future land use)**, **Developments**,
and **Subdivisions** GIS layers (primary sources the base analysis did not use) plus a multi-agent
web-research pass over city entitlement records and news.

> **Headline correction to the base analysis:** the supply threat is *larger and more concrete* than
> the base ranking implied — but for a different reason. The base analysis leaned on land *value* to
> infer development pressure. The city's **General Plan** is the real signal, and it shows the Kelton
> sits at the center of American Fork's **~444-acre Transit-Oriented Development (TOD) district**, of
> which **~116 acres is still vacant** and largely held by development entities. Meanwhile several
> tracts the base analysis ranked as watch-items are, per the General Plan, **not** apartment sites
> (very-low-density or environmentally-sensitive) and should be down-ranked.

## The finding that reframes the study — a ~116-acre vacant TOD land bank around the subject
American Fork's General Plan designates the Kelton **and the land around it** as **Transit-Oriented
Development** (the FrontRunner station is essentially at the subject). Within that 444-acre TOD
district, **33 vacant parcels totaling ~116 acres** remain, almost all within ~0.6 mi of the Kelton:

| Owner (entity) | Vacant acres in TOD | Note |
|---|---:|---|
| Individual / withheld (family land) | 71.2 | RA-zoned **today** but **TOD in the General Plan** — a rezone-in-waiting; the band immediately W of the subject |
| **BACH INVESTMENTS LLC** | 15.3 | Already zoned TOD; ~0.4 mi NW; assessed ~$7.0M |
| **SILVERADO PARTNERS LLC** | 13.0 | ~0.2–0.3 mi; TOD-area assemblage |
| **AF I-15 / AF 1-15 LLC** | 6.7 | freeway-adjacent TOD land |
| **OCAP AF TOD LLC** | 5.7 | entity named for "AF TOD" — assembled expressly for this |
| ROCKPORT LLC | 1.4 | |
| RH JOHNSON CONSTRUCTION INC | 1.1 | 518 W 200 S |
| YARD AF LLC ("The Yard") | 0.9 | |
| Utah Transit Authority | 0.3 | the transit agency's own station land |

~45 acres of this is **developer-entity-held**; ~71 acres is **family land the General Plan already
earmarks for TOD**. This is the dominant near-to-medium-term high-density competitive-supply threat —
an order of magnitude larger than the single 15-acre parcel the base ranking led with.

Two of these owners (Silverado Partners, OCAP AF TOD, AF I-15) fell into the base analysis's
"no public zoning (data gap)" bucket and were **dropped** from the candidate set — the City's zoning
polygon layer doesn't cover them, but the General Plan does. The General-Plan overlay recovers them.

## Active TOD multifamily is already delivering
American Fork's **Developments** layer (live site-plan tracker) shows, near the subject:
- **Meadowbrook TOD Phase 4 — Multi-Family, 123 units, "Under Review"** (~0.5 mi SE). Confirms the
  corridor is actively entitling *transit-oriented multifamily* right now, not just townhomes.
- Freeman Site Plan (retail, under review); Walmart Market fulfillment (retail).
- Farther out: Bridges at Fox Hollow (54 SF lots), Mira Vista Phase 4 (21 MF units), North Pointe
  Business Park.
The large vacant TOD parcels (BACH, the 98-ac band) are **not** yet in the Developments layer → no
site plan on file yet → they are **entitled-future**, not under-construction. Near-to-medium term.

## Per-site status — General Plan (future land use) vs current zoning
| # | Site / owner | Acres | Current zone | **General Plan (future)** | Recorded subdivision? | Reasoned status |
|---|---|---:|---|---|---|---|
| 1 | **BACH Investments** | 15.3 | AF **TOD** | **TOD** | No | **HIGH** — by-right dense residential/mixed-use; raw land, no site plan yet |
| 2 | **~98-ac band (W of subject)** | ~70 AF + ~29 Lehi | AF RA-1/RA-5; Lehi A-5 | **AF portion = TOD**; Lehi portion = Very-Low-Density Res-Ag / Commercial | No | **HIGH (AF ~70 ac)** — RA today but TOD-planned, abutting subject = rezone-in-waiting; Lehi ~29 ac Low |
| 3 | **Blue Spring Properties** | 23.2 | AF RA-5 | **Residential Very-Low Density** | No | **LOW** — city plans large-lot SF, *not* apartments (down-ranked from base "Medium") |
| 4 | **Lehi "PC" parcels** | 19.3 | Lehi PC | **Environmentally Sensitive Area** (wetlands nr Utah Lake; $18k/ac) | No | **LOW / non-developable** (down-ranked from base "Medium-Unknown") |
| 5 | **RH Johnson Construction** | 1.1 | AF **TOD** | **TOD** | No | **MEDIUM** — by-right TOD but small infill |
| 6 | **37-ac tract (Lehi, N)** | 37.2 | Lehi A-5 / C | **Commercial / Residential** | No | **MEDIUM (watch)** — Lehi GP allows residential; rezone candidate |
| 7 | **Windy City Development** | 51.4 | Lehi A-5 | **Very-Low-Density Res-Ag** | No | **LOW** — GP is large-lot ag-residential, not MF (down-ranked) |
| 8 | Harbor Enterprises | 8.6 | AF RA-5 | Residential Low Density | No | LOW — SF-planned |
| 9 | Walking the Wire | 17.2 | AF R1-12000 | Residential Low Density | No | LOW — single-family subdivision |
| 10 | Harbor View Development | 19.1 | AF PR-2.0 / SP | **Shoreline Protection** | No | LOW — non-developable lakeshore |

## What changed vs the base analysis
- **Elevated:** the ~98-ac band abutting the subject moves from "Medium/rezone-optionality" to **High**
  — the AF-side ~70 ac is *already TOD in the General Plan*. And the true high-density land bank is
  **~116 vacant TOD acres**, not one 15-ac parcel — held largely by named developers (Silverado,
  OCAP AF TOD, AF I-15) that the base run's zoning-gap filter had discarded.
- **Down-ranked (evidence contradicts "development-priced ⇒ apartment threat"):** Blue Spring
  (Very-Low-Density SF), Windy City (Very-Low-Density Res-Ag), and the Lehi "PC" tract
  (Environmentally Sensitive wetlands) are **not** apartment sites per the General Plan.
- **None of the target sites are recorded subdivisions yet** — the vacant land is entitled-future, not
  platted; the built/under-construction competition (Edgewater, Meadowbrook) is on *adjacent* blocks.

## Sources (primary GIS)
American Fork General Plan / Land_Use (`maps.afcity.org/.../Planning/Land_Use/MapServer/7`), Developments
(`.../Planning/Developments/MapServer/17`), Subdivisions (`.../Planning/Subdivisions/MapServer/0`),
Zoning2; Lehi General Plan (`services5.arcgis.com/.../Lehi_General_Plan`); Utah County LIR + ownership
layers (UGRC). Pulled 2026-07-13.

<!-- WEB-RESEARCH SYNTHESIS (multi-agent entitlement/news pass) appended below on completion -->
