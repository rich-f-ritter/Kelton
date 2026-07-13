#!/usr/bin/env python3
"""
build_map.py — Companion map for the 5-mile competitive Supply Chart.

Plots the subject and the competitive new-construction roster (same lifecycle
buckets the chart uses) on a satellite basemap: a 5-mile radius ring, numbered
pins that match the chart's row order, and per-property popups. Writes a single
branded, self-contained interactive **HTML** map (Leaflet bundled inline — no
CDN, no image dependencies).

Positions come from CoStar's exported Latitude/Longitude when present (the 5-mile
export is a true radius, so these are exact and in-radius); only comps lacking a
CoStar coordinate are geocoded (Nominatim, cached), preferring the hit closest to
the subject anchor. --subject-latlng "lat,lng" pins the subject exactly; otherwise
the subject's own roster coordinate is used.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import math
import os
import sys

import build_supply_chart as bc
import geo

MILE_M = 1609.34

# Bucket -> (hex colour, legend key, label). Colours match the workbook's section
# bands and the reference map.
BUCKET_STYLE = {
    "STABILIZED / STABILIZING": ("#2E75B6", "stab", "Stabilized / stabilizing"),
    "LEASING UP":               ("#ED7D31", "lease", "Leasing up"),
    "UNDER CONSTRUCTION":       ("#2FB344", "uc", "Under construction"),
    "PROPOSED":                 ("#FF0000", "prop", "Proposed pipeline"),
}
SUBJECT_GOLD = "#B49955"       # 5-mile ring
SUBJECT_STAR = "#FF00E5"       # subject marker — electric magenta, max contrast on
                               # satellite imagery and distinct from every bucket colour
SHADOW_COLOR = "#7C4DFF"



def _vendor(fname):
    """Read a bundled vendor asset (Leaflet). Looked up under the skill's
    assets/vendor/ (skill root) or scripts/assets/vendor/."""
    here = os.path.dirname(os.path.abspath(__file__))            # .../scripts
    for base in (os.path.dirname(here), here):                    # skill root, then scripts
        path = os.path.join(base, "assets", "vendor", fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
    raise FileNotFoundError(f"vendored asset not found: assets/vendor/{fname}")


def _ordered(props):
    """Comps in the EXACT order the workbook's Competitive Analysis numbers them, so
    the map pins match the chart's '#': by bucket, then earliest delivery first
    (undated last), then larger first. (Must mirror build_supply_chart's per-bucket
    sort — previously this sorted newest-first and the numbers were reversed.)"""
    order = {b[0]: i for i, b in enumerate(bc.BUCKET_ORDER)}

    def key(p):
        dated = p.deliv_year and p.deliv_q
        return (order.get(p.bucket, 99),
                bc.p_qi(p) if dated else 10 ** 9,
                -(p.units or 0))
    return sorted(props, key=key)


# --------------------------------------------------------------------------- #
# Map rendering
# --------------------------------------------------------------------------- #
def build_map(props, subject_name, subject_address, subject_latlng,
              out_path, shadow_rows=None, subject_meta=None):
    """Render the HTML map from **exact coordinates only** — no geocoding. The
    subject anchor must be supplied (subject_latlng), and every comp must carry a
    lat/lng; comps without one are silently skipped (the caller gates the whole
    map on completeness and asks the analyst for the missing coordinates)."""
    if not subject_latlng:
        raise SystemExit("build_map needs subject_latlng 'lat,lng'.")
    slat, slng = [float(x) for x in subject_latlng.split(",")]

    located = [(p, p.lat, p.lng) for p in _ordered(props)
               if p.lat is not None and p.lng is not None]

    # ---- shadow-supply sites — plotted only if the diligence row carries a
    # latitude/longitude (never geocoded) ----
    shadow_located = []
    for r in (shadow_rows or []):
        lat, lng = _num(r.get("latitude")), _num(r.get("longitude"))
        if lat is not None and lng is not None:
            shadow_located.append((r, lat, lng))

    counts = {b: {"n": 0, "u": 0} for b in BUCKET_STYLE}
    for p in props:
        if p.bucket in counts:
            counts[p.bucket]["n"] += 1
            counts[p.bucket]["u"] += p.units or 0

    _write_html(located, shadow_located, slat, slng, subject_name, subject_address,
                subject_meta or {}, counts, False, out_path)
    return len(located), False


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _pin_dict(num, name, bucket, color, lat, lng, units, deliver, occ, rent,
              owner, typ, dist, notes):
    return {"num": num, "name": name, "bucket": bucket, "color": color,
            "lat": round(lat, 6), "lng": round(lng, 6),
            "units": units, "deliver": deliver, "occ": occ, "rent": rent,
            "owner": owner or "—", "typ": typ or "—", "dist": dist,
            "notes": notes or ""}


def _write_html(located, shadow_located, slat, slng, subject_name, subject_address,
                smeta, counts, approx, out_path):
    # ---- subject pin ----
    pins = [_pin_dict(
        "S", subject_name, "SUBJECT", SUBJECT_STAR, slat, slng,
        smeta.get("units"), smeta.get("deliver"), None, None,
        smeta.get("owner"), smeta.get("typ"), 0.0,
        "Subject property — the underwriting target.")]
    # ---- comp pins (numbered in chart order) ----
    years = []
    for i, (p, plat, plng) in enumerate(located, 1):
        color, _bk, blabel = BUCKET_STYLE.get(p.bucket, ("#888", "x", p.bucket))
        if p.deliv_year:
            years.append(p.deliv_year)
        pins.append(_pin_dict(
            i, p.name, blabel, color, plat, plng, p.units, p.est_delivery or "TBD",
            round(p.occupancy * 100) if p.occupancy is not None else None,
            round(p.asking_rent) if p.asking_rent else None,
            p.owner, p.prop_type or p.style, round(p.proximity_mi, 1)
            if p.proximity_mi is not None else None,
            "; ".join(p.notes)))
    # ---- shadow pins ----
    for r, rlat, rlng in shadow_located:
        pins.append(_pin_dict(
            "•", r.get("property") or "Shadow site", "Shadow / latent supply",
            SHADOW_COLOR, rlat, rlng, _int(r.get("units")), r.get("est_delivery") or "TBD",
            None, None, None, None, None, r.get("notes") or r.get("status")))

    leg = [{"key": bk, "color": c, "label": lab,
            "n": counts[b]["n"], "u": counts[b]["u"]}
           for b, (c, bk, lab) in BUCKET_STYLE.items() if counts[b]["n"]]

    subj_units = smeta.get("units")
    subj_lab = f"Subject &mdash; {_html.escape(subject_name)}" + (
        f" ({subj_units:,}u)" if subj_units else "")
    yr_lo = min(years) if years else ""
    yr_hi = max(years) if years else ""
    yr_span = f"{yr_lo}&ndash;{yr_hi}" if years and yr_lo != yr_hi else (str(yr_lo) if years else "")
    loc_line = ", ".join([x for x in [smeta.get("city"), smeta.get("state")] if x]) \
        or _location_from_address(subject_address)
    xlsx = os.path.basename(out_path)
    if xlsx.endswith("__Map.html"):
        xlsx = xlsx[:-len("__Map.html")] + "__Supply_Chart.xlsx"
    else:
        xlsx = xlsx.replace("_Map.html", "_Supply_Chart.xlsx").replace(".html", ".xlsx")
    approx_note = (" Some pins are ZIP-approximate (geocode fell back)." if approx else "")

    doc = _TEMPLATE.format(
        title=_html.escape(f"{subject_name} — Competitive Supply"),
        leaflet_css=_vendor("leaflet.css"),
        leaflet_js=_vendor("leaflet.js"),
        kick=_html.escape(f"{subject_name}  —  Competitive Supply"),
        h1=("5-Mile New-Construction Supply" + (f"  ·  {loc_line}" if loc_line else "")),
        sub=(f"{len(located)} competitive properties"
             + (f" ({yr_span})" if yr_span else "")
             + " · bucketed by status · numbered to match the supply chart · "
               "click any pin for detail"),
        footer=(f"Companion to <b>{_html.escape(xlsx)}</b>. Positions from CoStar "
                "lat/lon (5-mi export) where available, else geocoded; distance is "
                f"straight-line from the subject.{approx_note}"),
        pins=json.dumps(pins),
        leg=json.dumps(leg),
        subj_lab=subj_lab,
        subj_units=subj_units or "",
        has_shadow=("true" if shadow_located else "false"),
        shadow_color=SHADOW_COLOR,
        gold=SUBJECT_GOLD,
        subj=SUBJECT_STAR,
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(doc)


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _location_from_address(address):
    city, state = geo.parse_city_state(address or "")
    return ", ".join([x for x in [city, state] if x])


_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<style>{leaflet_css}</style>
<style>
  :root{{--navy:#153D64;--blue:#589BD5;--gold:{gold};--subj:{subj};--gray:#6F6F70;--ink:#1A2B3C;}}
  html,body{{margin:0;height:100%;font-family:Calibri,'Segoe UI',Arial,sans-serif;color:#404040;}}
  #wrap{{display:flex;flex-direction:column;height:100%;}}
  header{{background:var(--navy);color:#fff;padding:10px 18px;}}
  header .kick{{font-size:11px;letter-spacing:3px;color:#B6D6EF;text-transform:uppercase;font-weight:bold;}}
  header h1{{margin:2px 0 0;font-family:Georgia,'Times New Roman',serif;font-weight:600;font-size:22px;}}
  header .sub{{font-size:12px;color:#cfe0ef;margin-top:2px;}}
  #map{{flex:1;}}
  footer{{background:#f3f4f6;color:var(--gray);font-size:11px;padding:6px 18px;border-top:1px solid #e5e7eb;}}
  .legend{{background:#fff;padding:9px 11px;border-radius:5px;box-shadow:0 1px 5px rgba(0,0,0,.3);font-size:12px;line-height:1.55;}}
  .legend b{{font-family:Georgia,serif;color:var(--navy);}}
  .legend .row{{display:flex;align-items:center;gap:7px;}}
  .legend .dot{{width:13px;height:13px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #999;flex:none;}}
  .legend .star{{color:var(--subj);font-size:17px;line-height:1;text-shadow:0 0 2px #fff;}}
  .legend .ct{{color:var(--gray);font-size:11px;}}
  .legend .ring{{width:13px;height:13px;border-radius:50%;border:2px dashed var(--gold);flex:none;}}
  .pin{{border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.45),0 1px 4px rgba(0,0,0,.55);color:#fff;
       font-weight:bold;text-align:center;font-family:Calibri,Arial,sans-serif;display:flex;
       align-items:center;justify-content:center;}}
  .pin.sub{{background:transparent;border:none;box-shadow:none;font-size:42px;color:var(--subj);
           text-shadow:0 0 4px #fff,0 0 4px #fff,0 0 7px #fff,0 1px 3px rgba(0,0,0,.65);}}
  .lp{{font-family:Calibri,Arial,sans-serif;max-width:290px;}}
  .lp h3{{margin:0 0 1px;font-family:Georgia,serif;color:var(--navy);font-size:15px;}}
  .lp .grp{{font-size:11px;letter-spacing:.5px;text-transform:uppercase;font-weight:bold;margin-bottom:6px;}}
  .lp .kv{{display:grid;grid-template-columns:auto auto;gap:1px 14px;font-size:12px;margin-bottom:5px;}}
  .lp .kv span:nth-child(odd){{color:var(--gray);}}
  .lp .kv b{{color:var(--ink);}}
  .lp .nt{{font-size:11px;color:#555;border-top:1px solid #eee;padding-top:5px;line-height:1.4;}}
</style>
</head>
<body><div id="wrap">
<header>
  <div class="kick">{kick}</div>
  <h1>{h1}</h1>
  <div class="sub">{sub}</div>
</header>
<div id="map"></div>
<footer>{footer}</footer>
</div>
<script>{leaflet_js}</script>
<script>
const PINS = {pins};
const LEG = {leg};
const HAS_SHADOW = {has_shadow};
const map = L.map('map',{{scrollWheelZoom:true}});
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:19, attribution:'Imagery &copy; Esri, Maxar, Earthstar Geographics'}}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:19, opacity:0.9}}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:19, opacity:0.9}}).addTo(map);

const sub = PINS.find(p=>p.num==='S');
L.circle([sub.lat,sub.lng],{{radius:5*1609.34, color:'{gold}', weight:2, dashArray:'6 6', fill:false}}).addTo(map);

const usd = v => v==null ? '—' : '$'+v.toLocaleString();
function popup(p){{
  const isSub = p.num==='S';
  return `<div class="lp">
    <h3>${{isSub?'★ ':(p.num==='•'?'':p.num+'. ')}}${{p.name}}</h3>
    <div class="grp" style="color:${{p.color}}">${{p.bucket}}</div>
    <div class="kv">
      <span>Units</span><b>${{p.units==null?'—':p.units.toLocaleString()}}</b>
      <span>Est. delivery</span><b>${{p.deliver||'—'}}</b>
      <span>Occupancy</span><b>${{p.occ==null?'—':p.occ+'%'}}</b>
      <span>Avg mkt rent</span><b>${{usd(p.rent)}}</b>
      <span>Type</span><b>${{p.typ}}</b>
      <span>Distance</span><b>${{p.dist==null?'—':'≈'+p.dist+' mi'}}</b>
      <span>Owner / sponsor</span><b>${{p.owner}}</b><span></span><span></span>
    </div>
    ${{p.notes?`<div class="nt">${{p.notes}}</div>`:''}}
  </div>`;
}}
const bounds = [];
PINS.forEach(p=>{{
  bounds.push([p.lat,p.lng]);
  let icon;
  if(p.num==='S'){{
    icon = L.divIcon({{className:'', html:`<div class="pin sub">★</div>`, iconSize:[44,44], iconAnchor:[22,38]}});
  }} else if(p.num==='•'){{
    icon = L.divIcon({{className:'', html:`<div class="pin" style="background:${{p.color}};width:16px;height:16px;font-size:9px;opacity:.9;"></div>`, iconSize:[16,16], iconAnchor:[8,8]}});
  }} else {{
    icon = L.divIcon({{className:'', html:`<div class="pin" style="background:${{p.color}};width:25px;height:25px;font-size:12px;">${{p.num}}</div>`, iconSize:[25,25], iconAnchor:[13,13]}});
  }}
  L.marker([p.lat,p.lng],{{icon, zIndexOffset: p.num==='S'?1000:0}}).addTo(map).bindPopup(popup(p));
}});
map.fitBounds(bounds,{{padding:[60,60]}});

const lg = L.control({{position:'bottomright'}});
lg.onAdd = function(){{
  const d = L.DomUtil.create('div','legend');
  let rows = LEG.map(b=>`<div class="row"><span class="dot" style="background:${{b.color}}"></span>${{b.label}} <span class="ct">(${{b.n}} · ${{b.u.toLocaleString()}}u)</span></div>`).join('');
  d.innerHTML = `<b>5-mi competitive supply</b><br>
   <div class="row"><span class="star">★</span> {subj_lab}</div>
   ${{rows}}
   ${{HAS_SHADOW?`<div class="row"><span class="dot" style="background:{shadow_color}"></span>Shadow / latent supply</div>`:''}}
   <div class="row"><span class="ring"></span> 5-mile radius</div>`;
  return d;
}};
lg.addTo(map);
</script>
</body></html>
"""


def _subject_meta(costar_roster_path, subject_name):
    key = bc.name_key(subject_name)
    for p in bc.parse_costar_roster(costar_roster_path):
        if bc.name_key(p.name) == key:
            return {"units": p.units, "owner": p.owner, "typ": bc.derive_type(p),
                    "deliver": (str(p.year_built) + " (built)") if p.year_built else None,
                    "city": p.city, "state": p.state}
    return {}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subject-name", required=True)
    ap.add_argument("--subject-address", default="")
    ap.add_argument("--subject-latlng", default=None,
                    help="Exact subject 'lat,lng' to override geocoding.")
    ap.add_argument("--costar-roster", required=True)
    ap.add_argument("--costar-analytics", required=True)
    ap.add_argument("--realpage", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--target", type=float, default=bc.DEFAULT_STABILIZATION_TARGET)
    ap.add_argument("--latlng", default=None,
                    help="CSV (property,latitude,longitude) of coordinates for comps "
                         "CoStar doesn't geolocate. Required to plot RealPage-only "
                         "pipeline deals — the map is only built once every comp has one.")
    ap.add_argument("--diligence", default=None,
                    help="Filled diligence CSV — applies researched corrections and "
                         "plots type=shadow rows (only those carrying a lat/lon).")
    args = ap.parse_args(argv)

    an = bc.parse_costar_analytics(args.costar_analytics)
    deliveries = an.deliveries
    as_of = bc.parse_as_of(args.as_of or an.complete_label or an.latest_label)
    props = bc.build_competitive_roster(
        args.costar_roster, args.realpage, deliveries, as_of,
        args.subject_name, args.subject_address, args.target)

    shadow_rows = None
    if args.diligence:
        rows = bc.load_diligence(args.diligence)
        bc.apply_diligence(props, rows)
        shadow_rows = [r for r in rows if r.get("type") == "shadow"]

    if args.latlng:
        bc.apply_latlng(props, bc.load_latlng(args.latlng))
    subj_ll = args.subject_latlng or bc.subject_latlng_from_roster(
        args.costar_roster, args.subject_name)
    bc.compute_proximity(props, subj_ll)      # exact lat/lon only, no geocoding
    bc.drop_beyond_radius(props)              # enforce the 5-mile radius
    missing = [p for p in props if p.lat is None or p.lng is None]
    if not subj_ll:
        sys.exit("Subject has no coordinate — pass --subject-latlng 'lat,lng'.")
    if missing:
        print(f"HTML map NOT built — {len(missing)} comp(s) lack a lat/lon:")
        for p in sorted(missing, key=lambda x: x.name):
            print(f"   {p.name}  [{'+'.join(sorted(p.sources))}]")
        sys.exit("Supply coordinates via --latlng (property,latitude,longitude) and retry.")
    placed, _ = build_map(props, args.subject_name, args.subject_address, subj_ll,
                          args.out, shadow_rows,
                          _subject_meta(args.costar_roster, args.subject_name))
    print(f"HTML map written: {args.out}  ({placed} properties, exact lat/lon)")


if __name__ == "__main__":
    sys.exit(main())
