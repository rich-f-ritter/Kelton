# Rent Comps – High Level: data-sourcing rules

The whole point of this format is that **each field comes from the right source**.
Get these right; they are the recurring mistakes.

## Which source for what
| Field | Source | Notes |
|---|---|---|
| Per-bedroom **rent** | **HelloData**, T{N}-day **executed** (default 90) | Average **asking ("market")** rent on units that went **off-market** (leased) in the trailing window. This is "executed market rent." |
| **Total – Effective** rent | **HelloData** effective, unit-weighted | Effective = net of concessions. |
| **Concession %** | derived | `1 − Effective ÷ Gross`. |
| Per-bedroom & total **SF** | **CoStar** avg SF by unit type | CoStar export must include `Studio/One/Two/Three Bedroom Avg SF`. HelloData is daily website pricing activity — **do NOT use it for SF**. |
| **Unit counts** (by bedroom) | **CoStar** for comps; **rent roll** for the subject | HelloData distinct-unit counts are unreliable (it's listing activity, not a census). |
| **Total units** | CoStar property total (may exceed the 1/2/3BR sum if CoStar leaves some uncategorized — set `units` explicitly, e.g. The Arden = 414 vs 390 detail). |
| **Occ %** | **CoStar** occupied (`1 − vacancy`) | shown as "Occ % (CoStar)". |
| **Leased %** | **HelloData**, computed | `1 − (distinct units currently listed available ÷ total distinct HD units)`. Shown alongside CoStar occ; the two differ by method — keep both. |
| **Distance** | geocode → straight-line from subject | Census geocoder first, Nominatim fallback. **Verify against the submarket clustering** — model/Supply-tab distances are often wrong (bad subject geocode). |

## HelloData "T-day executed" definition
A lease is "executed" in the window if its **Off Market Date** is within the last `t_days`
of `as_of`. For each property × bedroom, average `Last Asking Rent` (gross) and
`Last Effective Rent` (net). Blank cell = no executed lease in that bedroom in the window.

## Subject handling
- Unit **counts** and per-bedroom **SF** come from the **rent roll / underwriting intake**, not CoStar or HelloData.
- Subject is the **cream benchmark row**, excluded from the rent-heat color scale.

## Submarket clustering
Group comps into the analyst's submarket clusters (e.g., "Most relevant", "Behind <retail node>",
"To the West"). Each cluster gets a merged label, a faint cool tint, and a divider — this is the
row-distinction treatment (subtle, not zebra).

## Layout (matches the TMG model "Rent Comps – High Level" tab)
`# · Property · Group/Submarket · Owner · Yr · Dist · Occ%(CoStar) · Leased%(HD) · Conc · Units`
then per-bedroom **Studio / 1BR / 2BR / 3BR** each `# · SF · Rent`,
then **Total – Gross** `# · SF · Rent · PSF` and **Total – Effective** `Rent · PSF`.
Data columns (K…) are width 6.5; a light box frames each bedroom block; PSF = total rent ÷ total SF.

## Gotchas seen on real deals
- A brand-new building may not geocode (not in TIGER yet) — anchor the subject off a
  known adjacent point and hand-set its lat/lng.
- Co-located comps (same street) overlap on the map — fine; zoom separates them.
- Esri World Imagery tiles need internet at open time; Leaflet itself is inlined.
