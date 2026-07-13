# Land Use Analysis — The Kelton

**301 S 1100 W, American Fork, UT 84003** · competitive land-use / zoning / multifamily-supply-threat study · run 2026-07-13

## Deliverables (this folder)
| File | What it is |
|---|---|
| `The Kelton - Land Use Analysis.xlsx` | Self-documenting workbook — Overview, Assumptions & Decisions, Methodology, Data Sources, Land-Use / Zoning / MF-Threat crosswalks, a **Parcels** sheet (all 12,125 classified parcels), a **Vacant – Developable** sheet, and the reasoned **Top Vacant Threats**. |
| `The Kelton - Land Use Viewer.html` | Self-contained interactive map (Leaflet bundled, no CDN). Toggle **Land Use / Zoning / Vacant Threats**, satellite/streets basemap, hover for parcel detail, export PNG. |
| `The Kelton - Land Use Preview.png` | Land-use hero image of the 2-mile disc. |
| `The Kelton - Vacant Threats Preview.png` | Threat view — the vacant parcels ranked by apartment-supply threat. |
| `Vacant_Site_Status_Deep_Dive.md` | **Deeper follow-up** — exact status of each nearby vacant site from the AF/Lehi **General Plan / Developments / Subdivisions** layers + a 105-agent verified entitlement/records research pass. Read this for the per-site status detail. |
| `Tables/` | `top10_concerning_vacant.csv`, the three crosswalk CSVs, `decisions_log.md`, `unmapped_codes.json`. |
| `config.json`, `pull_merge.py` | The run's brain + the Utah-specific two-layer parcel pull (reproducible). |

## Headline (refined by the deep-dive — see `Vacant_Site_Status_Deep_Dive.md`)
The Kelton sits inside American Fork's **FrontRunner Station-Area / TOD district**. The supply threat
splits cleanly by horizon:

- **NEAR-TERM (0–3 yr) — townhomes-for-sale already in the ground next door.** **Edgewater** (=
  **D.R. Horton**, sales office 351 S 1110 W) and **Meadowbrook** (= **Woodside**, 853 W 560 S) are
  for-sale attached townhome communities — city-classified "Multifamily" — with multiple phases under
  construction and several completed in 2025, plus a **123-unit "Meadowbrook TOD Phase 4" MF building
  under review**. Real competition, but a different *tenure* (for-sale) than the Kelton's rentals.
- **LONGER-TERM (3–7 yr) — a ~116-acre developer-held TOD land bank wraps the subject.** Inside AF's
  ~444-acre TOD future-land-use area: **BACH Investments' 15.3-ac TOD parcel** (BACH = **Bach Homes**,
  a prolific apartment builder — 350–700 units/yr, the 285-unit Bach Homes AF Apartments, the 338-unit
  Elevate), plus **Silverado Partners (~13 ac)**, **OCAP AF TOD LLC (~6 ac)**, **AF I-15 LLC (~7 ac)**
  and **~71 ac of RA-zoned-but-TOD-planned** family land. Highest-density (60+ du/ac) if built.
- **Two key caveats:** (1) the TOD framework rides on the **American Fork Station Area Plan, which was
  still a PROPOSED (not adopted) General Plan Amendment as of Aug 2025** — pipeline, not fully in force;
  and (2) **no site plan is on file for the BACH parcel** — the apartment threat is credible but not
  shovel-ready.
- **Corrections (value ≠ entitlement):** Blue Spring (GP Residential Very-Low Density; part of its
  land is going to UTA/UDOT for FrontRunner ROW), the Lehi "PC" tract (3 du/ac + wetlands; apartments
  only via discretionary Area Plan), and Windy City (Very-Low-Density Res-Ag) are **down-ranked to Low**
  — they are *not* near-term apartment sites. **Bridges at Fox Hollow** is detached single-family (87
  lots), not multifamily.

**Net read for underwriting:** near-term competition is **for-sale townhomes** already under
construction adjacent to the subject; the large **rental-apartment** threat is a credible but
entitlement-dependent, **developer-held TOD land bank** (Bach Homes the anchor), not a Year-1/2 supply
shock. This squares with the supply-chart's modest near-term pipeline while flagging a genuine
long-horizon densification risk from the FrontRunner TOD build-out. Pair with the supply-chart for the
5-mi picture.

## Data & method (see `Tables/decisions_log.md` for the full audit)
- **Subject point verified** against the Utah County parcel footprint for "Kelton Apartments Phase 1
  Plat" (40.370787, −111.824874). The Census geocoder mis-matched the address to the wrong quadrant
  ("301 N 1100 E") and was overridden.
- **Parcels:** Utah County LIR (UGRC) for land use/acreage/value + a join to UGRC's ownership layer on
  PARCEL_ID for owner names. UGRC publishes owner only for **entity-owned** parcels (LLC/corp/gov) —
  which happen to be exactly the developer parcels that matter for a threat ranking.
- **Land use:** the county's coarse PROP_CLASS is enriched with the mass-appraisal building type to
  carve out Apartments/Multifamily, Commercial, Industrial, Agricultural, and Institutional (see log §4).
- **Zoning:** American Fork (city GIS) + Lehi (city AGOL), crosswalked to MF-threat against the
  ordinances (e.g. AF R3/R4/TOD = High; Lehi R-3/MU/TOD = High; Lehi **TH-5 = "Transitional Holding"**,
  a rezone-required holding zone, *not* a townhouse district). Zero unmapped codes.
- **Analysis area:** 2.0-mile radius (the near-in competitive area); the 5-mile pipeline lives in the
  supply-chart workstream.

## Regenerate
```
export LUA_ROOT=analysis/land-use
python3 .claude/skills/land-use-analysis/scripts/preflight.py --root analysis/land-use
python3 analysis/land-use/pull_merge.py --root analysis/land-use          # parcels (LIR + owner join)
python3 .claude/skills/land-use-analysis/scripts/pull_zoning.py --root analysis/land-use
python3 .claude/skills/land-use-analysis/scripts/run_all.py classify --root analysis/land-use
python3 .claude/skills/land-use-analysis/scripts/run_all.py prep     --root analysis/land-use
#   ... reason -> in/reasoned_ranking.json (already committed) ...
python3 .claude/skills/land-use-analysis/scripts/run_all.py deliver  --root analysis/land-use
```
(Heavy intermediates `in/*.geojson` and `in/_ck/` are git-ignored; they rebuild from the pull.)
