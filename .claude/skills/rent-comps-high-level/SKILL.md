---
name: rent-comps-high-level
description: >-
  Build the Milestone "Rent Comps – High Level" deliverable for a multifamily
  acquisition — a branded Excel workbook in the TMG model's high-level rent-comp
  layout, plus a self-contained interactive satellite map and a one-page preview
  image — from a HelloData unit-details CSV, a CoStar export (avg SF by bedroom +
  occupancy), and the subject's rent roll. Use whenever an analyst has chosen a
  set of rent comps for a deal and wants them assembled in the standard high-level
  format: HelloData T90-day executed rents, CoStar SF/occupancy, concession, rent
  heat, and submarket clustering. Encodes the per-field data-sourcing rules (which
  source for rents vs SF vs counts vs occupancy) so they are not re-derived wrong.
---

# Rent Comps – High Level

Produces three artifacts from one config:
1. **`*_High_Level.xlsx`** — the rent-comp table in the TMG model layout: identity +
   per-bedroom (`# · SF · Rent`) + Total-Gross + Total-Effective, with rent **heat**
   (color scale down each column), comps **grouped by submarket cluster**, and the
   subject as a cream benchmark row.
2. **`*_Map.html`** — self-contained Leaflet map on **satellite** imagery; subject =
   gold star, comps = numbered pins colored by cluster, rich popups (year, units, SF,
   CoStar occ / HD leased, T-day gross & effective rent, concession, per-bedroom table).
3. **`*_Preview.png`** — one-page PNG mirroring the Excel for quick eyeballing.

**Read `reference/methodology.md` first** — it is the authority on which source feeds
each field. Getting rents (HelloData executed), SF (CoStar by bedroom), counts (CoStar /
rent roll), and occupancy (CoStar occ vs HD leased) from the *right* place is the point.

## Inputs you gather per deal
- **HelloData unit-details CSV** (cols: `Property Name, Bedrooms, SF, Last Asking Rent,
  Last Effective Rent, On Market Date, Off Market Date, Unit, …`) covering the subject + comps.
- **CoStar export** that includes `Avg Unit SF`, unit counts by bedroom, `Vacancy %`, and
  **`Studio/One/Two/Three Bedroom Avg SF`** (the per-bedroom SF columns — request this
  export explicitly; the basic property list lacks them).
- **Subject rent roll / underwriting intake** for the subject's unit counts and per-bedroom SF.
- The analyst's **chosen comps**, grouped into **submarket clusters**.

## Workflow
1. Build a `config.json` (copy `scripts/config_example.json`). For each comp fill:
   `name, hd_key` (must match the HelloData `Property Name`), `cluster, owner, year,
   units` (CoStar total — set explicitly if it differs from the bedroom-count sum),
   `avg_sf, occ_costar` (CoStar), `counts` `[studio,1,2,3]` (CoStar), `bed_sf`
   `[studio,1,2,3]` (CoStar per-bedroom; use `null` where none), and `address`.
   Fill `subject` from the rent roll. Set `hellodata_csv, as_of, t_days, title,
   submarket, sources`.
2. **Geocode** for the map: `python scripts/geocode.py config.json` (Census→Nominatim;
   writes `lat/lng/dist`). **Eyeball the printed distances against the clusters** and
   hand-fix outliers (a new building may not geocode — anchor the subject manually).
3. **Build:**
   ```
   python scripts/build_workbook.py config.json  Deal_Rent_Comps_High_Level.xlsx
   python scripts/build_map.py      config.json  Deal_Rent_Comps_Map.html
   python scripts/build_preview.py  config.json  Deal_Rent_Comps_Preview.png   # optional
   ```
4. Spot-check the preview / open the map; deliver the xlsx + html (+ png).

## Requirements
`pip install pandas openpyxl matplotlib` (matplotlib only for the preview). Leaflet JS/CSS
are bundled in `scripts/lib/` and inlined into the HTML, so the map is self-contained —
only the satellite tiles fetch at open time (needs internet in the viewer's browser).

## Conventions (don't drift)
- Per-bedroom **rent = HelloData T{t_days}-day executed asking**; Total-Effective = HD
  effective; Concession = `1 − Eff/Gross`.
- **SF always from CoStar** (per-bedroom + property avg); subject SF/counts from the rent roll.
- **Occ % = CoStar occupied**, shown next to **Leased % = HelloData**.
- Brand palette: navy `#074070`, blue `#589BD5`, gold `#B49955`; serif titles, Calibri body;
  rent heat pale-red→white→pale-blue; subject row cream `#FFF6E6`.
