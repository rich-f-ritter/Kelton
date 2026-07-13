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

---

# Web-Research Synthesis (multi-agent entitlement & records pass)

*105 verification agents · 22 sources fetched · 89 claims extracted → 23 confirmed / 2 refuted ·
adversarial 3-vote verification (2/3 refutes to kill). Full run archived in the workflow transcript.*

## Who the owners actually are, and what is (and isn't) entitled

| Site / owner | Verified status | Product / units | Horizon | Key source |
|---|---|---|---|---|
| **1. BACH Investments LLC** — 15.3 ac TOD (13:038:0068) | **Owner = Bach Homes** (Draper; Shon Rindlisbacher), a prolific apartment developer (350–700 units/yr; built 285-unit Bach Homes AF Apartments 2021, 338-unit Elevate). Holds ~67 Utah County parcels. **No site plan / development agreement on file** for this parcel. | TOD permits 60+ du/ac; product unfiled | **Longer-term (3–7 yr)** — highest ceiling, real developer, no filed project | Utah County land records; bachhomes.com; AF PC records |
| **TOD framework — AF Station Area Plan** | **Still a PROPOSED General Plan Amendment** (PC recommendation Aug 20, 2025); Council adoption + MAG certification not confirmed. 509-ac CRA area, I-15→Utah Lake. | — | pipeline, **not yet in force** | utah.gov/pmn PC agenda 8/20/25; Psomas; KUTV |
| **2. ~98-ac band (W of subject)** | **Ownership MIXED, largely unresolved** (individual names withheld). Control 13:041:0044 = Allred family (individual); 13:041:0080 = **Blue Spring LLC**, part **quit-claimed to UTA + UDOT easement (Apr-2026)** for FrontRunner double-track ROW. AF-side ~70 ac is **TOD in the General Plan**. No rezone/plat verified. | RA now / TOD-planned | **Longer-term, entitlement-dependent** | Utah County AbstractReverse / SerialByEntry; AF GP |
| **3. Blue Spring Properties LLC** — 23 ac | AF GP **Residential Very-Low Density**; no plan/rezone/listing verified. | large-lot SF | **down-ranked → Low** | AF GP; Utah County records |
| **4. Lehi 'PC' parcels** — 19 ac | Lehi PC base **3 du/ac**; apartments (12)/townhomes (8) only via **discretionary Area Plan**; also mapped Environmentally Sensitive; ~$18k/ac greenbelt value. No Area Plan on file. | discretionary only | **down-ranked → Low / long-horizon** | Lehi Dev Code Ch.6; Lehi GP |
| **5. RH Johnson Construction** — ~1 ac (13:042:0028 +0062/0063) | **PC recommended 6-0 (Jan 8, 2025) to rezone PI-1 → TOD** — but staff-initiated **map cleanup, no project**; one parcel listed for sale; ROW dedication + FrontRunner double-tracking complicate it. | TOD if adopted; small | **Medium** (advancing, no project) | AF PC minutes 01/08/2025 |
| **6. Windy City Development** — 51 ac | Lehi GP **Very-Low-Density Res-Ag**; no verified activity (status unresolved). | large-lot ag-res | **Low** | Lehi GP |
| **7. Harbor Enterprises / Harbor View** | No verified development activity; near Utah Lake / Shoreline Protection. | — | **Low** | (coverage gap) |
| **8. Walking the Wire** — 17 ac | R1-12000 / GP Residential Low Density; no verified activity. | single-family | **Low** | AF GP |
| **Edgewater (D.R. Horton)** — 1110–1160 W / 480–530 S | **Real, entitled, delivering**: multiple phases under construction (4-28-26), phase Lots 243-248 **completed 12-23-25**; sales office 351 S 1110 W; ~$400–483k. | for-sale attached **townhomes** (city-classified Multifamily) | **NEAR-TERM (in the ground)** | AF Active/Pending report; drhorton.com |
| **Meadowbrook (Woodside — 'Regency at Meadowbrook')** — 500–540 S / 700–800 W | **Real, actively selling/delivering**: ~10 phases, ~half completed 2025; sales 853 W 560 S; ~$468–495k. Plus **'Meadowbrook TOD Phase 4' = 123 MF units under review** (AF Developments GIS). | for-sale **townhomes** + 123-unit MF bldg | **NEAR-TERM** | AF Active/Pending report; woodsidehomes.com; AF Developments GIS |
| **Bridges at Fox Hollow** — 1080 N 350 E | **Detached single-family / cottages, 87 lots (33 cottages + 54 SF)** — NOT apartments/townhomes. | detached SF | no MF threat | thebridgesatfoxhollow.com; afcitizen.com |
| **Elevate at 620 / 'Bach High Pointe'** (context) | Elevate = 338-unit apt community (2024), = Lake City Row Ph 2 (~2,500-unit PC master plan, Vest Annexation 2019); Ph 3 includes 'Bach High Pointe' 144 apts + 16 TH. **~2 mi EAST** of the Kelton = citywide, not adjacent. | apartments | citywide, not adjacent | apartments.com; AF DRC records |

**Refuted (do not rely on):** (a) that the Station Area is "already two-thirds built out"; (b) that
"High Pointe Apartments, 695 E 620 S" is an approved apartment project with a unit count — it is only
"application under review" (6-23-26) and may be conflated with the east-side "Bach High Pointe."

**Open (unresolved) questions:** whether BACH has since filed a TOD site plan; the remaining owners of
the ~98-ac assemblage and whether any is being platted; whether the Station Area Plan GPA has been
formally adopted since Aug 2025 and its total programmed unit count; and the current status of
Windy City / Harbor / Walking-the-Wire (unresolved, not confirmed inactive).

## Bottom line for underwriting
- **Near-term (0–3 yr) competition is townhomes-for-sale already under construction next door**
  (Edgewater = D.R. Horton, Meadowbrook = Woodside) — a different *tenure* than the Kelton's rentals,
  plus one 123-unit MF building under review. Real, but for-sale attached product, not a wave of new rentals.
- **The large rental-apartment threat is a credible but entitlement-dependent, developer-held ~116-ac
  TOD land bank** (Bach Homes/BACH the anchor) — high ceiling, no shovel-ready project, and riding on a
  TOD plan that was still proposed, not adopted. A 3–7 yr risk to monitor, not a Year-1/2 supply shock.
- **Several "development-priced" tracts are NOT apartment sites** (Blue Spring, Lehi PC, Windy City) —
  the General Plan and Lehi code cap them at low density; value ≠ entitlement.
- This is consistent with the deal's supply-chart (modest near-term pipeline) while flagging a real
  long-horizon densification risk driven by the FrontRunner TOD build-out around the subject.

*Primary web sources: AF Planning Commission minutes 01/08/2025; AF Community Development Active/Pending
Projects report; utah.gov/pmn PC agendas (8/20/25); Psomas AF TOD; KUTV; Utah County land records
(BACH name search, AbstractReverse 13:041:0080); bachhomes.com; D.R. Horton Edgewater; Woodside Regency
at Meadowbrook; live-elevate.com; Lehi Development Code Ch. 6; Lehi FrontRunner Station Area Plan.*
