# Land Use Analysis — The Kelton

**301 S 1100 W, American Fork, UT 84003** · competitive land-use / zoning / multifamily-supply-threat study · run 2026-07-13

## Deliverables (this folder)
| File | What it is |
|---|---|
| `The Kelton - Land Use Analysis.xlsx` | Self-documenting workbook — Overview, Assumptions & Decisions, Methodology, Data Sources, Land-Use / Zoning / MF-Threat crosswalks, a **Parcels** sheet (all 12,125 classified parcels), a **Vacant – Developable** sheet, and the reasoned **Top Vacant Threats**. |
| `The Kelton - Land Use Viewer.html` | Self-contained interactive map (Leaflet bundled, no CDN). Toggle **Land Use / Zoning / Vacant Threats**, satellite/streets basemap, hover for parcel detail, export PNG. |
| `The Kelton - Land Use Preview.png` | Land-use hero image of the 2-mile disc. |
| `The Kelton - Vacant Threats Preview.png` | Threat view — the vacant parcels ranked by apartment-supply threat. |
| `Tables/` | `top10_concerning_vacant.csv`, the three crosswalk CSVs, `decisions_log.md`, `unmapped_codes.json`. |
| `config.json`, `pull_merge.py` | The run's brain + the Utah-specific two-layer parcel pull (reproducible). |

## Headline
The Kelton sits **inside American Fork's single most active new-housing corridor**, so the
competitive-supply threat is real but overwhelmingly a **townhome/attached + TOD** story, not
large garden-apartment tracts.

- **#1 threat — a 15.3-acre investor-owned parcel in the FrontRunner TOD zone, ~0.4 mi NW**, where
  dense residential is buildable **by-right** (station on 200 S; the city's Station Area Plan clusters
  multifamily within a half-mile; UTA double-tracking underway). Land is priced for development
  (~$460k/acre).
- **#2 — a ~98-acre band of development-priced vacant land abutting the subject (0.23 mi)**. Zoned
  low-density residential-agricultural (apartments *not* by-right today), but valued at $400–470k/acre
  and being platted/permitted for attached product **right now**: American Fork's project log shows
  dozens of **Edgewater Townhomes** and **Meadowbrook** multifamily phases under construction on the
  480–540 S / 700–1160 W blocks around the subject. Rezoning momentum — which AF is granting — is the risk.
- Then **Blue Spring** (23 ac RA-5, developer-owned), a **Lehi Planned-Community** tract (19 ac,
  plan-dependent), and small **TOD infill**.
- **Screened out as non-threats:** Utah Lake shoreline (Shoreline Protection / Marina), UDOT highway
  parcels, single-family-zoned tracts (deliver houses, not apartments), and government/HOA land.

**Net read for underwriting:** genuinely large **by-right garden-apartment** sites near the Kelton
are scarce; most by-right MF capacity is smaller TOD infill, and the biggest land banks still need a
rezone. But the corridor is being actively densified with townhome/attached product, so **new
competitive units will keep arriving immediately around the subject** — consistent with the
supply-chart's read that near-term deliveries are modest but the location is a growth magnet. Pair
this with the supply-chart (5-mi pipeline & absorption) for the full supply picture.

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
