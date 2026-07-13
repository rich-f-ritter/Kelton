"""Custom parcel pull for Utah County: the UGRC LIR layer carries the rich land-use
attributes (PROP_CLASS, building type, acreage, values, year built) but withholds owner
names; the companion UGRC ownership layer carries OWNERNAME keyed on PARCEL_ID. This
step pulls the LIR layer (reusing the skill's robust POST/objectId-paging fetcher),
joins owner on PARCEL_ID, derives a synthetic land-use code from PROP_CLASS + the county
mass-appraisal building type, and writes in/parcels_all.geojson in the normalized schema
the rest of the pipeline expects. (Replaces the generic pull_parcels for this run.)
"""
import json
import sys
from pathlib import Path

import requests
import urllib3

import os
_here = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(_here, "..", "..", ".claude", "skills", "land-use-analysis", "scripts")
sys.path.insert(0, SKILL)
import arcgis  # noqa: E402
import config as C  # noqa: E402
import geo  # noqa: E402

urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0"}


def synth_code(prop_class, binfo):
    pc = (prop_class or "").strip()
    b = (binfo or "").strip().lower()
    if pc == "Vacant":
        return "VAC"
    if pc == "Tax Exempt":
        return "EXEMPT"

    def has(*subs):
        return any(s in b for s in subs)

    MF = ("apartment", "multiple_residence", "unit_building", "triplex", "fourplex", "duplex",
          "multi_res", "group_care", "assisted_living", "retirement", "senior")
    INST = ("school", "hospital", "community_recreation", "recreation_center", "gymnasium",
            "classroom", "pavilion", "restroom", "museum", "home_for_the_elderly", "elderly")
    IND = ("indust", "mfg", "manufactur", "warehouse", "distribution", "flex", "mini_warehouse",
           "storage_garage", "storage_warehouse", "material_storage", "material_shelter",
           "parking_structure", "parking_garage", "laborator", "quonset_commercial", "secure_storage")
    COM = ("store", "shop", "office", "retail", "restaurant", "hotel", "motel", "bank", "market",
           "showroom", "mall", "shopping_center", "car_wash", "dealership", "automotive", "supermarket",
           "theater", "mortuary", "day_care", "clinic", "dental", "medical", "spa", "fitness",
           "bowling", "tavern", "snack", "convenience", "discount", "veterinary", "laundry",
           "barber", "health_club", "country_club", "service_garage", "mini_lube", "mini-mart",
           "fast_food", "commercial")
    AG = ("barn", "farm", "greenhouse", "stable", "dairy", "poultry", "loafing", "equestrian",
          "horse_arena", "hay", "silo", "concrete_stave", "concrete_poured", "kennel", "agricultur",
          "quonset", "livestock", "sun_shelter", "implement", "fruit_packing")
    SF = ("residence_single_family", "single_family", "detached", "one_story", "two_story",
          "bi-level", "split_level", "one_and_one_half", "cabin", "a-frame", "guest_house",
          "livable_space", "int:", "end:", "attached", "one-section", "two-section")
    if has(*MF):
        return "MF"
    if has(*INST):
        return "EXEMPT"
    if has(*IND):
        return "IND"
    if has(*COM):
        return "COM"
    if has(*AG):
        return "AG"
    if has(*SF):
        return "SF"
    if pc == "Commercial":
        return "COM"
    if pc == "Residential":
        return "SF"
    return "OTHER"


def fetch_owner_map(url, bbox, verify):
    """Light attribute-only join: page objectIds, pull PARCEL_ID+OWNERNAME (no geometry)."""
    oid_field, ids = arcgis.get_ids(url, bbox, "1=1", verify)
    omap = {}
    for i in range(0, len(ids), 1000):
        p = {"objectIds": ",".join(map(str, ids[i:i + 1000])),
             "outFields": "PARCEL_ID,OWNERNAME,OWN_TYPE", "returnGeometry": "false", "f": "json"}
        j = requests.post(url, data=p, headers=H, timeout=180, verify=verify).json()
        for f in j.get("features", []):
            a = f.get("attributes", {})
            pid = a.get("PARCEL_ID")
            if pid:
                omap[str(pid)] = (a.get("OWNERNAME"), a.get("OWN_TYPE"))
    return omap


def main():
    cfg = C.load()
    IN = C.indir(cfg)
    ck = IN / "_ck"
    poly = geo.analysis_polygon(cfg)
    bbox = geo.bbox(cfg)

    src = cfg["parcel_sources"][0]
    print(f"LIR parcels: {src['name']} ...", file=sys.stderr)
    raw = arcgis.fetch_all(src["url"], bbox, where="1=1", out_fields="*",
                           verify=src.get("verify_ssl", True), page=int(src.get("page", 1000)),
                           ck_dir=ck, label="Parcels_Utah_LIR")
    inpoly = arcgis.keep_in_poly(raw, poly)
    print(f"  fetched {len(raw)} -> in-area {len(inpoly)}", file=sys.stderr)

    osrc = cfg["owner_source"]
    print(f"owner join: {osrc['name']} ...", file=sys.stderr)
    omap = fetch_owner_map(osrc["url"], bbox, src.get("verify_ssl", True))
    print(f"  owner records: {len(omap)}", file=sys.stderr)

    feats, seen = [], {}
    for ft in inpoly:
        p = ft.get("properties", {}) or {}
        pid = str(p.get("PARCEL_ID") or "").strip()
        if not pid or ft.get("geometry") is None:
            continue
        if pid in seen:  # dedupe duplicate LIR rows; keep the larger-acre record
            if (p.get("PARCEL_ACRES") or 0) <= seen[pid]:
                continue
        seen[pid] = p.get("PARCEL_ACRES") or 0
        owner, own_type = omap.get(pid, (None, None))
        prop_class = p.get("PROP_CLASS")
        binfo = p.get("BLDG_SQFT_INFO")
        code = synth_code(prop_class, binfo)
        total = p.get("TOTAL_MKT_VALUE")
        land = p.get("LAND_MKT_VALUE")
        impr = (total - land) if (isinstance(total, (int, float)) and isinstance(land, (int, float))) else None
        feats.append({"type": "Feature", "geometry": ft["geometry"], "properties": {
            "account": pid, "owner": owner, "situs": p.get("PARCEL_ADD"),
            "landuse_code": code, "legal": p.get("SUBDIV_NAME"),
            "county": "Utah", "impr_value": impr, "total_value": total,
            "year_built": p.get("BUILT_YR"), "data_confidence": "full",
            "source": src["name"],
            # extra context carried for the workbook / reasoning (ignored by classify):
            "prop_class": prop_class, "bldg_type": binfo, "land_value": land,
            "own_type": own_type, "house_cnt": p.get("HOUSE_CNT"),
            "bldg_sqft": p.get("BLDG_SQFT"), "subdiv": p.get("SUBDIV_NAME")}})

    # dedupe: rebuild keeping only the winning row per PARCEL_ID
    best = {}
    for f in feats:
        pid = f["properties"]["account"]
        ac = f["properties"].get("total_value") or 0
        prev = best.get(pid)
        if prev is None or (f["properties"].get("bldg_sqft") or 0) >= (prev["properties"].get("bldg_sqft") or 0):
            best[pid] = f
    out_feats = list(best.values())

    matched = sum(1 for f in out_feats if f["properties"]["owner"])
    out = IN / "parcels_all.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": out_feats,
                               "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}}))
    from collections import Counter
    cc = Counter(f["properties"]["landuse_code"] for f in out_feats)
    print(f"Wrote {len(out_feats)} parcels -> {out}  (owner matched {matched}/{len(out_feats)})")
    print("  synthetic land-use codes:", dict(cc))


if __name__ == "__main__":
    main()
