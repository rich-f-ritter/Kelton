#!/usr/bin/env python3
"""
subject_intake.py — subject rent/occupancy rows straight from RAW files, so the
supply-chart skill runs **independently of the rr-t12-processor skill**.

It ports only the piece of that skill the supply chart needs: the subject's
**mix-weighted** market/effective rent from a HelloData "Unit Details" CSV, plus a
monthly physical-occupancy read from a T-12. Returns the same
{(year, month): {mkt, eff, occ, conc}} shape as parse_intake_subject(), so the
downstream TTM aggregation is unchanged.

Methodology carried over (matches the rr-t12-processor's Lease Trend tab):
- HelloData rows are executed (off-market) leases with an asking + effective rent
  and a floor plan. For each month, each floor plan's leases are averaged, then
  the plans are **mix-weighted by unit count** (units per plan) — never a flat
  average across leases. Concession % = 1 − effective/asking (from gross rents).
- Occupancy per month = 1 − |Vacancy Loss| / Potential Rent (AGPR) from the T-12,
  read by line name (Potential Rent, else Market Rent + Gain/Loss to Lease; and
  Vacancy Loss).
"""
from __future__ import annotations

import csv
import re
import datetime as _dt
from collections import defaultdict

import openpyxl


# --------------------------------------------------------------------------- #
# HelloData — mix-weighted monthly market & effective rent
# --------------------------------------------------------------------------- #
def _to_date(s):
    if not s:
        return None
    s = str(s).strip()[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _f(v):
    try:
        return float(str(v).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _plan_key(s):
    """Base floor-plan key for mix-weighting. Collapses tier variants that share a
    plan (e.g. 'Phoenix', 'Phoenix E', 'Phoenix P' -> 'phoenix') so a plan's units
    are grouped and weighted together, matching the intake's base-plan convention."""
    p = re.sub(r"\s+", " ", str(s or "").strip())
    p = re.sub(r"\s+[A-Za-z]$", "", p)          # drop a trailing single-letter tier
    return p.lower()


_NAME_NOISE = re.compile(r"\b(apartments?|apts?|townhomes?|homes?|the|at|on|of)\b", re.I)


def _name_key(name):
    """Normalized property-name key (mirrors build_supply_chart.name_key)."""
    n = _NAME_NOISE.sub(" ", str(name or "").lower())
    return re.sub(r"\s+", " ", n).strip()


def parse_hellodata(path, property_name=None):
    """Read a HelloData 'Unit Details' CSV -> list of row dicts (or [] if absent).

    Works with both the subject-only export and the 5-mile multi-property export
    (one CSV covering every comp): pass `property_name` to filter to one property.
    Matching is by normalized name, with a token-containment fallback so
    "255 Assay" matches "255 Assay Street Luxury Apartments". If the CSV carries
    no 'Property Name' column (subject-only pull), all rows are returned.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        return []
    if not rows or not property_name or "Property Name" not in rows[0]:
        return rows
    key = _name_key(property_name)
    exact = [r for r in rows if _name_key(r.get("Property Name")) == key]
    if exact:
        return exact
    # containment fallback: one name's tokens are a subset of the other's
    want = set(key.split())
    hits = {}
    for r in rows:
        k = _name_key(r.get("Property Name"))
        toks = set(k.split())
        if want and toks and (want <= toks or toks <= want):
            hits.setdefault(k, []).append(r)
    if len(hits) == 1:                       # unique fuzzy match only
        return next(iter(hits.values()))
    return []


def hellodata_monthly_mixweighted(rows):
    """{(year, month): {mkt, eff, conc, n}} — each floor plan's monthly executed
    asking/effective rents averaged, then **mix-weighted by the plan's unit count**
    (distinct units in the HelloData). This is the subject market-rent signal."""
    if not rows:
        return {}
    # unit-count weight per floor plan = distinct units seen with that plan
    units_by_plan = defaultdict(set)
    for r in rows:
        units_by_plan[_plan_key(r.get("Floorplan"))].add(str(r.get("Unit") or "").strip())
    weights = {p: len(u) for p, u in units_by_plan.items()}

    # per (month, plan) collect asking / effective of leases that went off-market
    cell = defaultdict(lambda: {"ask": [], "eff": []})
    months = set()
    for r in rows:
        od = _to_date(r.get("Off Market Date"))
        if not od:
            continue
        ym = (od.year, od.month)
        months.add(ym)
        c = cell[(ym, _plan_key(r.get("Floorplan")))]
        for fld, key in (("Last Asking Rent", "ask"), ("Last Effective Rent", "eff")):
            v = _f(r.get(fld))
            if v and v > 0:
                c[key].append(v)

    out = {}
    for ym in months:
        na = da = ne = de = 0.0
        n = 0
        for plan, w in weights.items():
            c = cell.get((ym, plan))
            if not c:
                continue
            if c["ask"]:
                na += (sum(c["ask"]) / len(c["ask"])) * w
                da += w
            if c["eff"]:
                ne += (sum(c["eff"]) / len(c["eff"])) * w
                de += w
                n += len(c["eff"])
        a = na / da if da else 0.0
        e = ne / de if de else 0.0
        rec = {}
        if a:
            rec["mkt"] = a
        if e:
            rec["eff"] = e
        if a > 0 and e > 0:
            rec["conc"] = 1 - e / a
        if n:
            rec["n"] = n
        if rec:
            out[ym] = rec
    return out


# --------------------------------------------------------------------------- #
# HelloData — per-property CURRENT stats for the comp roster (5-mile export)
# --------------------------------------------------------------------------- #
def hellodata_rows_by_property(path):
    """Split a multi-property HelloData CSV into {normalized_name: rows}.
    Returns {} for a subject-only export (no 'Property Name' column)."""
    rows = parse_hellodata(path)
    if not rows or "Property Name" not in rows[0]:
        return {}
    out = {}
    for r in rows:
        out.setdefault(_name_key(r.get("Property Name")), []).append(r)
    return out


def hellodata_property_stats(rows, total_units=None, trailing_days=90,
                             lease_up=False):
    """Current-state read of one property from its HelloData unit rows:

    - `ask` / `eff`: **mix-weighted** asking & effective rent from leases executed
      (off-market) in the trailing window — per floor plan averaged, then weighted
      by the plan's distinct-unit count (same convention as the subject rows /
      the model's Cash Flow Annual HelloData rents). Falls back to the latest
      asking rents of active listings if nothing leased in the window.
    - `occ` (lease-ups only, `lease_up=True`): cumulative lease-up occupancy =
      distinct units ever leased (off-market) minus units back on the market,
      over `total_units`. The naive availability proxy (1 − active/total) badly
      OVERSTATES a lease-up (never-yet-listed units aren't occupied) and slightly
      understates stabilized assets (pre-marketing of future move-outs), so
      stabilized occupancy is deliberately left to CoStar/RealPage.
    - `pace`: distinct units leased per month over the trailing window.
    - `n_leases`: lease count behind `ask`/`eff`.
    """
    if not rows:
        return {}
    dates = [d for d in (_to_date(r.get("Off Market Date")) or
                         _to_date(r.get("On Market Date")) for r in rows) if d]
    if not dates:
        return {}
    asof = max(dates)
    cutoff = asof - _dt.timedelta(days=trailing_days)

    units_by_plan = defaultdict(set)
    for r in rows:
        units_by_plan[_plan_key(r.get("Floorplan"))].add(str(r.get("Unit") or "").strip())
    weights = {p: len(u) for p, u in units_by_plan.items()}

    def mixweight(sel_rows, fld):
        per_plan = defaultdict(list)
        for r in sel_rows:
            v = _f(r.get(fld))
            if v and v > 0:
                per_plan[_plan_key(r.get("Floorplan"))].append(v)
        num = den = 0.0
        for plan, vals in per_plan.items():
            w = weights.get(plan, 1)
            num += (sum(vals) / len(vals)) * w
            den += w
        return (num / den) if den else None

    executed = [r for r in rows
                if (_to_date(r.get("Off Market Date")) or _dt.date.min) >= cutoff]
    active = [r for r in rows if not _to_date(r.get("Off Market Date"))]

    rec = {"asof": asof}
    src = executed if executed else active
    rec["ask"] = mixweight(src, "Last Asking Rent")
    rec["eff"] = mixweight(src, "Last Effective Rent")
    rec["n_leases"] = len({str(r.get("Unit") or "").strip() for r in executed})
    rec["pace"] = rec["n_leases"] / (trailing_days / 30.0)
    if total_units and lease_up:
        unit = lambda r: str(r.get("Unit") or "").strip()
        leased_ever = {unit(r) for r in rows if _to_date(r.get("Off Market Date"))}
        active_units = {unit(r) for r in active}
        rec["occ"] = max(0.0, min(1.0, len(leased_ever - active_units) / total_units))
    return {k: v for k, v in rec.items() if v is not None}


# --------------------------------------------------------------------------- #
# T-12 — monthly physical occupancy (light, name-based read; no full categorizer)
# --------------------------------------------------------------------------- #
_MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
     "Nov", "Dec"], start=1)}


def _month_of(v):
    m = re.search(r"([A-Za-z]{3,})[\s\-/]+(\d{4})", str(v or ""))
    if m and m.group(1)[:3].lower() in _MONTHS:
        return int(m.group(2)), _MONTHS[m.group(1)[:3].lower()]
    return None


def t12_monthly_occupancy(path):
    """{(year, month): occupancy 0-1} from a T-12 operating statement.

    occupancy = 1 − |Vacancy Loss| / Potential Rent (AGPR). AGPR is the 'Potential
    Rent' line if present, else Market Rent + Gain/Loss to Lease. Returns {} if the
    lines can't be found (the subject occupancy row is then left to the analyst)."""
    if not path:
        return {}
    ws = openpyxl.load_workbook(path, data_only=True).active
    # month header row = the row with the most parseable "Mon YYYY" cells
    hdr_r, colmap, best = None, {}, 0
    for r in range(1, min(15, ws.max_row) + 1):
        cm = {}
        for c in range(1, ws.max_column + 1):
            ym = _month_of(ws.cell(r, c).value)
            if ym:
                cm[c] = ym
        if len(cm) > best:
            best, hdr_r, colmap = len(cm), r, cm
    if not colmap:
        return {}

    def label(r):
        for c in (2, 1, 3):
            v = ws.cell(r, c).value
            if isinstance(v, str) and v.strip():
                return v.strip().lower()
        return ""

    gpr = ltl = pot = vac = None
    for r in range(hdr_r + 1, ws.max_row + 1):
        lbl = label(r)
        if not lbl:
            continue
        if pot is None and "potential rent" in lbl:
            pot = r
        elif gpr is None and "market rent" in lbl and "loss" not in lbl:
            gpr = r
        elif ltl is None and ("loss to lease" in lbl or "loss-to-lease" in lbl):
            ltl = r
        elif vac is None and "vacancy" in lbl and "gain" not in lbl:
            vac = r
    if vac is None or (pot is None and gpr is None):
        return {}

    def cell(r, c):
        return _f(ws.cell(r, c).value) or 0.0 if r else 0.0

    out = {}
    for c, ym in colmap.items():
        agpr = cell(pot, c) if pot else (cell(gpr, c) + cell(ltl, c))
        v = cell(vac, c)                      # vacancy loss (negative)
        if agpr:
            out[ym] = max(0.0, min(1.0, 1 + v / agpr))
    return out


# --------------------------------------------------------------------------- #
# Combined — the parse_intake_subject() drop-in
# --------------------------------------------------------------------------- #
def subject_monthly_from_raw(hellodata_csv=None, t12_path=None, subject_name=None):
    """{(year, month): {mkt, eff, occ, conc}} for the subject rows, computed from
    raw files (HelloData CSV + T-12) — no intake workbook required. Pass
    `subject_name` when the CSV is a multi-property (5-mile) export so only the
    subject's rows feed the mix-weighting."""
    out = (hellodata_monthly_mixweighted(parse_hellodata(hellodata_csv, subject_name))
           if hellodata_csv else {})
    occ = t12_monthly_occupancy(t12_path)
    for ym, o in occ.items():
        out.setdefault(ym, {})["occ"] = o
    return out
