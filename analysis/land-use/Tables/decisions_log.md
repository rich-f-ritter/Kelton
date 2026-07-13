# Land Use Analysis — The Kelton (301 S 1100 W, American Fork, UT 84003) — Decisions Log

Prepared 2026-07-13. All GIS pulled live from public sources this session (open internet).

## 1. Subject location (verified point)
- **Verified point: lat 40.370787, lon -111.824874** (WGS84).
- Verified against the Utah County LIR parcel footprint for **"Kelton Apartments Phase 1 Plat"**
  (serials 44-238-0002…0015, situs "301 S 1100 W UNIT E…N", built 2023). The point is the
  union centroid of the developed condo-plat parcels.
- **Mailing address mis-geocoded.** The US Census onelineaddress geocoder matched
  "301 S 1100 W" to **"301 N 1100 E"** (lat 40.383186, lon -111.769161) — the wrong quadrant
  (N/E instead of S/W), ~2.9 mi ENE. Rejected in favor of the parcel footprint.
- The title entity on the developed parcels is **MWIC KELTON LLC**; the adjacent commercial
  parcel **44-238-0001 (257 S 1100 W)** is **MWIC KELTON COMMERCIAL LLC** — the "omitted
  commercial parcel" flagged in the deal's cross-workstream review.

## 2. Analysis area
- **2.0-mile geodesic radius** around the verified point (skill default; `analysis_area.mode=radius`).
- Captures west/central **American Fork** and east/central **Lehi** (the immediate competitive
  area), plus a corner of **Saratoga Springs** and unincorporated/Utah-Lake land to the SW.
- The broader 5-mile competitive set is intentionally left to the deal's separate **supply-chart**
  workstream; this study is the finer-grained "what could be built right next door" view.

## 3. Parcel data source(s) + coverage
- **Primary: Utah County Parcels LIR** (UGRC statewide LIR schema), ArcGIS Online, item
  69477c1143924bc9990cdb930b033fb5 →
  `services1.arcgis.com/99lidPhWCzftIe9K/.../Parcels_Utah_LIR/FeatureServer/0`.
  Rich attributes: PROP_CLASS, PARCEL_ACRES, TOTAL/LAND_MKT_VALUE, BUILT_YR, BLDG_SQFT_INFO
  (county mass-appraisal building type), HOUSE_CNT, SUBDIV_NAME. **12,125 parcels** in the radius.
- **Owner join: Utah County Parcels** (UGRC ownership schema, same host,
  `.../Parcels_Utah/FeatureServer/0`) joined on **PARCEL_ID**. The LIR schema withholds owner
  names; the companion layer supplies **OWNERNAME**.
  - **Owner coverage is partial and NON-random: UGRC publishes owner names only for
    entity-owned parcels (LLC / corp / government); individually-owned (natural-person)
    parcels are blank for privacy.** County-wide only ~30% of parcels carry a name; in-radius
    coverage runs 75-90% for Commercial/Industrial, 42-43% for Multifamily/Vacant, and just
    8% for Single-Family. **This concentrates owner data on exactly the developer/investor
    parcels that matter for a supply-threat ranking** (every named vacant parcel in the top-10
    is an LLC/corp/agency). Blank owners are treated as "individual (name withheld)".
- Both hosts are UGRC ArcGIS Online (`*.arcgis.com`) — reachable; no city self-hosted parcel
  server was needed. Utah County's own server (`maps.utahcounty.gov`) returned 401 and was not used.
- Custom step `pull_merge.py` replaces the generic `pull_parcels` to do the two-layer join +
  synthetic land-use derivation (below); it reuses the skill's robust `arcgis.py` fetcher.

## 4. Land-use source & granularity (synthetic codes)
- The county's standardized **PROP_CLASS is coarse** (only Residential / Commercial / Vacant /
  Tax Exempt / Unknown / blank) — it cannot by itself separate apartments from houses or retail
  from warehouses. A **synthetic land-use code** is derived per parcel:
  1. PROP_CLASS = **Vacant → VAC**; **Tax Exempt → EXEMPT**.
  2. Otherwise the county building type (**BLDG_SQFT_INFO**) carves out use:
     apartments / multiple_residence / N-unit / tri-/four-plex / duplex / senior-multi → **MF**;
     school/hospital/rec/civic → **EXEMPT**; warehouse/mfg/storage/auto → **IND**;
     store/office/retail/hotel/restaurant/medical → **COM**; barn/farm/greenhouse/stable → **AG**;
     single-family/detached/one-/two-story/townhome-attached → **SF**.
  3. Fallback on PROP_CLASS: Commercial→COM, Residential→SF, Unknown/blank→**OTHER**.
- **Known limitation:** BLDG_SQFT_INFO reflects the parcel's *primary* building, so a
  single-family lot whose largest record is a shed can read as SF via fallback (correct), and
  ~2,500 parcels with no class/building signal land in **Other / Unclassified** (honest gap,
  many are condo or utility sub-parcels). MF identification is reliable *where the building
  type is populated* (the Kelton's own condo parcels correctly read "multiple_residence" → MF).
- The `public_owner_regex` additionally routes government / school / church / district / UDOT /
  irrigation owners to **Public / Airport / Institutional** regardless of code.
- **"Vacant" definition:** county PROP_CLASS = Vacant (unimproved). Agricultural greenbelt land
  is classed Agricultural/Rural, NOT Vacant, so it is not counted as a by-right apartment site.

## 5. Zoning sources + honest gaps
- **American Fork** — city self-hosted ArcGIS: `maps.afcity.org/.../Planning/Zoning2/MapServer/0`
  (fields ZONECLASS/ZONEDESC; esriJSON; SSL not verified). Preflight **reachable (HTTP 200)** —
  the usual "self-hosted city box is unreachable" risk did not materialize here, so no
  substitution was needed. 142 polygons in-area.
- **Lehi** — ArcGIS Online: `services5.arcgis.com/rObWD7PYeLl9jJPT/.../Lehi_Zoning/FeatureServer/0`
  (field Zone). 157 polygons in-area.
- **Gaps (labeled, not faked):** the Saratoga Springs corner, unincorporated Utah County, and
  Utah Lake/shore have **no public zoning layer here** → rendered as the "No public zoning
  (data gap)" class and **excluded from the vacant-threat candidate set** (71 vacant parcels
  dropped for no-zoning). Coverage is complete for the developed American Fork + Lehi land that
  surrounds the subject, which is what matters for near-in supply.

## 6. Zoning crosswalk corrections (verified against the ordinances)
- **American Fork:** R3-7500 / R4-7500 → Multifamily, **High** (R4 confirmed to allow multifamily).
  **TOD** → Mixed Use, **High** (form-based, dense residential by-right; FrontRunner station area,
  200 S). R2-7500 → Two-Family, Low. **PR-2.0/2.3/3.0** (Planned Residential) and **PC** →
  Planned/Overlay, **Unknown** (reasoned per site; PR densities are low, ~2-3 du/acre). R1-* → SF,
  Low. Commercial/office/industrial/marina/shoreline → Low.
- **Lehi:** R-3 → Multifamily, **High** (High-Density Residential). **MU** and **TOD** → Mixed Use,
  **High** (residential by-right; TOD has no fixed max density). R-2.5 → Townhouse/Med, Medium.
  **TH-5 = "Transitional Holding"** → Agricultural/Rural, **Low** (a HOLDING zone — development
  requires a rezone; NOT a townhouse district, despite the "TH" prefix — a deliberate correction).
  **RC = "Resort Community"** → Planned/Overlay, **Unknown** (master-planned; can include MF).
  **T-M** (technology/manufacturing) and BP/LI/H-I → Industrial, Low. C/C-H/C-I/HC/NC/CR → Commercial,
  Low. A-1/A-5 → Agricultural, Low. R-1-* → SF, Low.
- Result: **zero unmapped land-use or zoning codes** after classification.
- Land use and zoning kept **independent** (a Commercial- or RA-zoned parcel can still carry MF use);
  neither layer was used to "correct" the other.

## 7. Mechanical pre-filters (before reasoning)
`prepare_candidates` reduced 520 vacant parcels to 60 developable parcels → 39 owner/adjacency
clusters by dropping: **387 under 1.0 acre**, **71 in the no-zoning data gap**, **2 non-developer
(gov/HOA) owners**, plus road/sliver shapes (Polsby-Popper < 0.16). Government/HOA/church-owned
vacant land is additionally removed by the owner rule in classification.

## 8. Vacant-threat assessment — reasoned (see in/reasoned_ranking.json)
- Threat is a **judgment**, not a score. The mechanical candidates were reasoned against: (a) the
  county land VALUE per acre (development-grade $400-470k vs raw/farm $18-60k), (b) proximity and
  submarket, (c) owner type (entity/developer vs individual/holding), and (d) **demonstrated
  entitlement momentum** from American Fork's own Community Development project log (dozens of
  Edgewater Townhome + Meadowbrook multifamily phases under construction on the 480-540 S /
  700-1160 W blocks around the subject) and the FrontRunner **TOD Station Area Plan**.
- **#1 threat:** a 15.3-ac investor-owned **TOD** parcel 0.4 mi NW (by-right dense residential).
- **#2:** a ~98-ac development-priced vacant band **abutting the subject** (RA-zoned but being
  entitled for attached product in real time) — elevated to Medium/High-Watch on rezoning momentum.
- Then Blue Spring (23 ac RA-5, developer), Lehi PC (19 ac, plan-dependent), and small TOD infill.
- **Screened OUT as non-threats:** Shoreline Protection (66 ac lakeshore, non-developable), Marina
  (M-1) land, UDOT highway parcels, and single-family-zoned tracts (deliver houses, not apartments).
- **Net read:** the supply threat is genuine but skewed to TOWNHOME/attached and TOD product; large
  by-right garden-apartment sites are scarce, and the biggest land banks need a rezone (which AF is
  granting — so momentum, not current entitlement, is the risk).

## 9. Sources & vintage
- Utah County Parcels LIR + Parcels (UGRC / Utah Geospatial Resource Center), current as of the
  layer's CURRENT_ASOF (Oct 2025 vintage); pulled 2026-07-13.
- American Fork zoning (`maps.afcity.org`, city GIS) and Lehi zoning (Lehi City AGOL), pulled 2026-07-13.
- American Fork City Community Development "Report on Projects" (active/pending/under-construction),
  americanfork.gov DocumentCenter/View/18060 (entitlement momentum evidence).
- American Fork TOD / FrontRunner Station Area Plan (Psomas; KSL; city Capital Projects); Lehi
  Development Code (Ch. 5 zoning districts, amlegal/lehi-ut.gov) for the zoning crosswalk.
- Subject geocode cross-check: US Census onelineaddress (Public_AR_Current) — mis-match documented.

## 10. Deep-dive refinement (follow-up — see Vacant_Site_Status_Deep_Dive.md)
The reasoned ranking above was refined with two primary sources the base pass did not use — the
American Fork & Lehi **General Plan (future land use)**, **Developments**, and **Subdivisions** GIS
layers, and a **105-agent verified entitlement/records research pass** — which materially changed
several calls (the ranking in in/reasoned_ranking.json reflects the refined view):
- **General Plan > land value.** The base pass inferred development pressure from $/acre; the City's
  General Plan is the real signal. The Kelton sits in AF's **~444-ac TOD future-land-use area**, of
  which **~116 ac is still vacant** and largely developer-held (BACH/Bach Homes 15 ac, Silverado
  Partners 13 ac, OCAP AF TOD 6 ac, AF I-15 7 ac, plus ~71 ac RA-zoned-but-TOD-planned family land).
  Three of these owners had been **dropped by the no-zoning filter** (§7) — the AF zoning polygon layer
  doesn't cover them, but the General Plan does; the GP overlay recovers them.
- **#2 (98-ac band) elevated to High (longer-term):** its AF-side ~70 ac is RA-zoned today but
  **TOD in the General Plan** — a rezone-in-waiting. But ownership is **mixed** (Allred family +
  Blue Spring LLC), unresolved, and part (serial 13:041:0080) is being taken by **UTA/UDOT for
  FrontRunner double-track ROW** — so it is raw TOD land, not an entitled project.
- **Down-ranked to Low (value ≠ entitlement):** Blue Spring (GP Residential Very-Low Density), the
  Lehi PC parcels (PC base 3 du/ac + Environmentally-Sensitive/greenbelt; apartments only via
  discretionary Area Plan), and Windy City (GP Very-Low-Density Res-Ag).
- **RH Johnson (Site 5)** contradicts "unentitled": PC recommended a PI-1→TOD rezone 6-0 on 1/8/2025,
  but it is a staff map-cleanup with no project (kept Medium).
- **Owner identity verified:** BACH Investments LLC = **Bach Homes** (Draper; Shon Rindlisbacher), an
  active apartment developer — raising the #1 site's credibility even absent a filed site plan.
- **Near-term supply identified:** Edgewater (D.R. Horton) and Meadowbrook (Woodside) are for-SALE
  attached townhomes (city-classified "Multifamily") already delivering adjacent; Bridges at Fox
  Hollow is detached SF (not MF). **Key caveat:** the TOD framework (Station Area Plan GPA) was still
  **PROPOSED, not adopted** as of Aug 2025.
- Added sources: AF General Plan / Developments / Subdivisions GIS (`maps.afcity.org`); Lehi General
  Plan GIS; AF Planning Commission minutes 01/08/2025; utah.gov/pmn PC agendas (8/20/25); Utah County
  land records (BACH name search; AbstractReverse 13:041:0080); bachhomes.com; D.R. Horton Edgewater;
  Woodside Regency at Meadowbrook; Lehi Development Code Ch. 6.
