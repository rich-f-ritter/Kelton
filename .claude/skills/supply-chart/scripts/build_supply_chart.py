#!/usr/bin/env python3
"""
build_supply_chart.py — Automate the 5-mile new-construction Supply Chart.

Reads the three market exports (CoStar property roster, CoStar Data Analytics
time series, RealPage roster) for a subject property's 5-mile radius, reconciles
them into a single competitive-supply roster, buckets each property by lifecycle
stage, pins delivery quarters against the CoStar quarterly deliveries series, and
writes a formatted workbook with:
  - "Competitive Analysis": the colour-coded, chronological roster.
  - "Supply & Absorption": a relative-year (TTM) forecast of new supply,
    absorption, and overall occupancy with editable demand scenarios and pipeline
    toggles; plus subject rent/occupancy/concession rows (with --intake and
    --costar-subject-rents).
  - "Reconciliation Log": per-property merged values, sources, and conflicts.

See SKILL.md for the full methodology. Proximity (miles) is computed by geocoding
the subject and each comp (Nominatim, cached; offline ZIP-centroid fallback).
Verified lease-up rent/occupancy from HelloData is left flagged for the analyst.

Usage:
    python build_supply_chart.py \
        --subject-name "Canyon Ridge" \
        --subject-address "2552 E Gowen Rd" \
        --costar-roster   examples/canyon_ridge/CoStar_5mi_50unit_properties.xlsx \
        --costar-analytics examples/canyon_ridge/CoStar_5mi_Data_Analytics.xlsx \
        --realpage        examples/canyon_ridge/Realpage_5mi.xlsx \
        --out             output/Canyon_Ridge__Supply_Chart.xlsx
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from typing import NamedTuple, Optional

import openpyxl
import geo
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# --------------------------------------------------------------------------- #
# Tunable thresholds (documented in SKILL.md)
# --------------------------------------------------------------------------- #
DEFAULT_STABILIZATION_TARGET = 0.95
# A delivered property is "stabilized" once occupancy >= this; recently delivered
# (within ~2 years) and below it = still "leasing up".
STABILIZED_OCC = 0.90
# How far back a delivery counts as "new construction" worth charting.
NEW_CONSTRUCTION_LOOKBACK_YEARS = 4

# --------------------------------------------------------------------------- #
# Styling (sampled from the reference template)
# --------------------------------------------------------------------------- #
NAVY = "FF153D64"        # matches the TMG model's section-header navy
BLUE = "FF2E75B6"
STEEL = "FFD6E0F0"       # light steel band (sub-headers / consensus row)
GOLD = "FFFFE699"        # accent for the TMG "our growth" row
GRAY = "FFF2F2F2"
WHITE = "FFFFFFFF"
YELLOW = "FFFFFF00"
INPUT_BLUE = "FF0000FF"  # model convention: blue font = editable input

THIN = Side(style="thin", color="FFBFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def fill(color: str) -> PatternFill:
    return PatternFill("solid", fgColor=color)


def font(bold=False, size=9, color="FF000000", italic=False):
    return Font(name="Calibri", bold=bold, size=size, color=color, italic=italic)


CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center")
RIGHT = Alignment(horizontal="right", vertical="center")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]


def quarter_index(year: int, q: int) -> int:
    """Absolute quarter index for ordering / arithmetic."""
    return year * 4 + (q - 1)


def fmt_quarter(year: int, q: int) -> str:
    return f"Q{q} {year}"


@dataclass
class Prop:
    name: str
    address: str
    units: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    year_built: Optional[int] = None
    construction_begin: Optional[str] = None
    status_raw: str = ""               # e.g. Existing / Stabilized / Pre-Planned
    costar_status: str = ""            # Existing / Under Construction / Proposed
    rp_status: str = ""                # Stabilized / Lease-Up / Under Construction / Pre-Planned / Planned
    # Per-source occupancy / rent so the two can be compared (not just merged).
    costar_occ: Optional[float] = None
    costar_rent: Optional[float] = None     # CoStar asking rent / unit
    rp_occ: Optional[float] = None
    rp_rent: Optional[float] = None         # RealPage effective rent / unit
    rp_asking: Optional[float] = None       # RealPage asking rent / unit (if exported)
    # Resolved primary values (chosen by source priority) used on the chart.
    occupancy: Optional[float] = None
    eff_rent: Optional[float] = None
    asking_rent: Optional[float] = None     # market/asking rent shown on the roster
    owner: Optional[str] = None
    stories: Optional[int] = None
    style: Optional[str] = None        # RealPage property style
    lat: Optional[float] = None        # CoStar-exported latitude (authoritative)
    lng: Optional[float] = None        # CoStar-exported longitude
    sources: set = field(default_factory=set)
    # HelloData per-property stats (5-mile export coverage)
    hd_ask: Optional[float] = None     # HD mix-weighted asking rent (trailing 90d)
    hd_eff: Optional[float] = None     # HD mix-weighted effective rent
    hd_occ: Optional[float] = None     # HD availability-based occupancy
    hd_pace: Optional[float] = None    # HD units leased / month (trailing 90d)
    # derived
    est_delivery: Optional[str] = None     # "Q2 2023" or None (undated pipeline)
    deliv_year: Optional[int] = None
    deliv_q: Optional[int] = None
    deliv_src: Optional[str] = None    # "CoStar property analytics" | "estimated" | ...
    bucket: Optional[str] = None
    prop_type: Optional[str] = None
    proximity_mi: Optional[float] = None   # straight-line miles subject -> comp
    roster_row: Optional[int] = None     # row on the Competitive Analysis sheet
    notes: list = field(default_factory=list)

    def note(self, txt: str):
        if txt and txt not in self.notes:
            self.notes.append(txt)


# --------------------------------------------------------------------------- #
# Address normalization & matching
# --------------------------------------------------------------------------- #
_STREET_NOISE = re.compile(
    r"\b(apartments?|apts?|townhomes?|the|at|on|of)\b", re.I)


def addr_key(address: str) -> Optional[str]:
    """Build a match key from a street address: leading number + first word.

    Handles ranges ("2410-2490 W Canal St" -> 2410) and directionals.
    """
    if not address:
        return None
    a = str(address).strip().lower()
    m = re.match(r"(\d+)", a)
    if not m:
        return None
    number = m.group(1)
    rest = a[m.end():].strip(" -")
    # drop a trailing range number like "-2490"
    rest = re.sub(r"^\d+\s*", "", rest)
    toks = [t for t in re.split(r"[\s,]+", rest) if t]
    # skip leading directional (n/s/e/w)
    dirs = {"n", "s", "e", "w", "ne", "nw", "se", "sw",
            "north", "south", "east", "west"}
    sig = next((t for t in toks if t not in dirs), toks[0] if toks else "")
    return f"{number} {sig}"


def name_key(name: str) -> str:
    n = _STREET_NOISE.sub(" ", str(name or "").lower())
    return re.sub(r"\s+", " ", n).strip()


# Tokens that mark a DIFFERENT phase/building of a similarly named project —
# containment across one of these must never fuzzy-match ("Bluewater at
# Balmoral" vs "... II"; "Residences at Kingwood" vs "... East").
_PHASE_TOKENS = {"i", "ii", "iii", "iv", "v", "1", "2", "3", "4", "5",
                 "east", "west", "north", "south", "phase", "ph"}


def _containment_ok(a: set, b: set) -> bool:
    """True if one token set contains the other AND the extra tokens are generic
    (not phase/direction markers)."""
    if not a or not b or not (a <= b or b <= a):
        return False
    return not ((a ^ b) & _PHASE_TOKENS)


def make_name_matcher(names):
    """Build a matcher over a set of canonical property names (e.g. the keys of a
    HelloData / per-property-analytics index). Returns fn(query_name) -> canonical
    key or None. Exact normalized match first; else a UNIQUE token-containment
    match ("255 Assay" -> "255 Assay Street Luxury Apartments") — but never across
    a phase marker ("Bluewater at Balmoral II" must not borrow "Bluewater at
    Balmoral"'s data), and never when ambiguous."""
    keyed = {}
    for n in names:
        keyed.setdefault(name_key(n), n)

    def match(query):
        k = name_key(query)
        if k in keyed:
            return keyed[k]
        want = set(k.split())
        if not want:
            return None
        hits = [ck for ck in keyed if _containment_ok(want, set(ck.split()))]
        return keyed[hits[0]] if len(hits) == 1 else None
    return match


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def _hdr_map(ws):
    headers = {}
    for j, c in enumerate(next(ws.iter_rows(min_row=1, max_row=1)), 1):
        if c.value is not None:
            headers[str(c.value).strip()] = j
    return headers


def _int(v):
    try:
        if v in (None, "", "-", "—"):
            return None
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _float(v):
    try:
        if v in (None, "", "-", "—"):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_costar_roster(path) -> list[Prop]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    h = _hdr_map(ws)

    def col(row, key):
        j = h.get(key)
        return row[j - 1] if j else None

    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = col(row, "Property Name")
        if not name:
            continue
        # CoStar v2 adds asking rent and vacancy; v1 lacks them.
        rent = _float(col(row, "Avg Asking/Unit"))
        vac = _float(col(row, "Vacancy %"))   # whole-percent, e.g. 8 -> 8%
        occ = (1 - vac / 100.0) if vac is not None else None
        p = Prop(
            name=str(name).strip(),
            address=str(col(row, "Property Address") or "").strip(),
            city=(str(col(row, "City")).strip() if col(row, "City") else None),
            state=(str(col(row, "State")).strip() if col(row, "State") else None),
            zipcode=(str(col(row, "Zip")).strip()[:5] if col(row, "Zip") else None),
            units=_int(col(row, "Number of Units")),
            year_built=_int(col(row, "Year Built")),
            construction_begin=(str(col(row, "Construction Begin")).strip()
                                if col(row, "Construction Begin") else None),
            status_raw=str(col(row, "Building Status") or "").strip(),
            costar_status=str(col(row, "Building Status") or "").strip(),
            costar_occ=occ,
            costar_rent=rent,
            owner=(str(col(row, "Owner Name")).strip()
                   if col(row, "Owner Name") else None),
            stories=_int(col(row, "Number of Stories")),
            # CoStar's own lat/lon (newer exports). Authoritative — the 5-mi export
            # is a true radius, so these give exact, in-radius positions and remove
            # the geocoding guesswork for every CoStar-listed property.
            lat=_float(col(row, "Latitude")),
            lng=_float(col(row, "Longitude")),
        )
        p.sources.add("CoStar")
        out.append(p)
    return out


def parse_realpage(path) -> list[Prop]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    h = _hdr_map(ws)

    def col(row, key):
        j = h.get(key)
        return row[j - 1] if j else None

    def col_any(row, keys):
        for k in keys:
            v = col(row, k)
            if v is not None:
                return v
        return None

    # RealPage exports effective rent; some pulls also carry an asking/market
    # rent column. Capture it if present (never use effective rent as "asking").
    # Two shapes are handled: the classic 5-mile roster (Name, Address, Total
    # Units, Property Status, ...) and the newer "Grid Performance" export, which
    # carries only Name + performance columns (Effective Rent, Occupancy, ...) —
    # no address/units/status. Grid rows still merge into the roster by name and
    # contribute their rent/occupancy.
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = col(row, "Name") or col(row, "Property Name")
        if not name:
            continue
        occ = _float(col(row, "Occupancy"))
        if occ is not None and occ > 1.5:      # percent (95.7) -> fraction
            occ /= 100.0
        p = Prop(
            name=str(name).strip(),
            address=str(col(row, "Address") or "").strip(),
            city=(str(col(row, "City")).strip() if col(row, "City") else None),
            state=(str(col(row, "State")).strip() if col(row, "State") else None),
            zipcode=(str(col(row, "Zip Code")).strip()[:5] if col(row, "Zip Code") else None),
            units=_int(col(row, "Total Units")),
            year_built=_int(col(row, "Year Built")),
            status_raw=str(col(row, "Property Status") or "").strip(),
            rp_status=str(col(row, "Property Status") or "").strip(),
            rp_occ=occ,
            rp_rent=_float(col(row, "Effective Rent")),
            rp_asking=_float(col_any(row, ("Asking Rent", "Market Rent",
                                           "Asking Rent / Unit", "Avg Asking Rent"))),
            owner=(str(col(row, "Property Owner")).strip()
                   if col(row, "Property Owner") else None),
            stories=_int(col(row, "Stories")),
            style=(str(col(row, "Property Style")).strip()
                   if col(row, "Property Style") else None),
        )
        p.sources.add("RealPage")
        out.append(p)
    return out


_QRE = re.compile(r"(\d{4})\s*Q([1-4])")


class Analytics(NamedTuple):
    """Parsed CoStar Data Analytics time series (see parse_costar_analytics)."""
    latest_inv: Optional[int]          # inventory units at the newest row (may be QTD)
    deliveries: dict                   # {(y, q): delivered units}
    latest_label: Optional[str]        # newest period label, e.g. "2026 Q3 QTD"
    series: dict                       # {(y, q): {inventory, deliveries, ...}}
    latest_uc: Optional[int]           # under-construction units at the newest row
    qtd: frozenset                     # {(y, q)} quarters that are partial (QTD)
    complete_label: Optional[str]      # newest COMPLETE quarter, e.g. "2026 Q2"


def parse_costar_analytics(path) -> Analytics:
    """Parse the CoStar Data Analytics quarterly time series.

    Each series entry has inventory, deliveries, occupancy_units, absorption,
    occupancy_pct, uc_units, eff_rent for that quarter. A "QTD" row (the current,
    partial quarter) is kept in the series but flagged in `qtd`; `complete_label`
    is the newest complete quarter — the default analysis (Y0) anchor, so a
    10-day-old quarter never masquerades as a full TTM window.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    h = _hdr_map(ws)
    pcol = h.get("Period")
    cols = {
        "inventory": h.get("Inventory Units"),
        "deliveries": h.get("Deliveries Units"),
        "occ_units": h.get("Occupancy Units"),
        "absorption": h.get("Absorption Units"),
        "occ_pct": h.get("Occupancy Percent"),
        "uc_units": h.get("Under Construction Units"),
        "eff_rent": h.get("Effective Rent Per Unit"),
    }
    deliveries = {}
    series = {}
    qtd = set()
    latest_inv = None
    latest_label = None
    latest_uc = None
    complete_label = None
    for row in ws.iter_rows(min_row=2, values_only=True):
        period = row[pcol - 1] if pcol else None
        if not period:
            continue
        m = _QRE.search(str(period))
        if not m:
            continue
        year, q = int(m.group(1)), int(m.group(2))
        rec = {k: (_float(row[c - 1]) if c else None) for k, c in cols.items()}
        series[(year, q)] = rec
        if "qtd" in str(period).lower():
            qtd.add((year, q))
        d = _int(rec["deliveries"])
        if d:
            deliveries[(year, q)] = d
        if latest_inv is None:  # rows are newest-first
            latest_inv = _int(rec["inventory"])
            latest_label = str(period).strip()
            latest_uc = _int(rec["uc_units"])
        if complete_label is None and "qtd" not in str(period).lower():
            complete_label = fmt_quarter(year, q)
    return Analytics(latest_inv, deliveries, latest_label, series, latest_uc,
                     frozenset(qtd), complete_label)


# --------------------------------------------------------------------------- #
# Reconciliation
# --------------------------------------------------------------------------- #
def reconcile(costar: list[Prop], realpage: list[Prop]) -> list[Prop]:
    """Merge the two rosters by address (primary) / name (fallback)."""
    merged: dict[str, Prop] = {}
    by_name: dict[str, str] = {}

    def same_property(a: Prop, b: Prop) -> bool:
        """Guard against merging two distinct properties that share an address
        (e.g. an existing asset and its planned redevelopment on the same site)."""
        ta = {t for t in name_key(a.name).split() if len(t) >= 4}
        tb = {t for t in name_key(b.name).split() if len(t) >= 4}
        if ta & tb:
            return True                       # share a real name token -> same
        # no name overlap: an existing asset vs a pipeline deal = different
        a_pipe = _proposed_signal(a) or _uc_signal(a)
        b_pipe = _proposed_signal(b) or _uc_signal(b)
        if (a_pipe and _existing_signal(b)) or (b_pipe and _existing_signal(a)):
            return False
        if a.year_built and b.year_built and abs(a.year_built - b.year_built) > 5:
            return False
        if a.units and b.units and abs(a.units - b.units) > 0.25 * max(a.units, b.units):
            return False
        return True

    def register(p: Prop):
        ak = addr_key(p.address)
        if ak and ak in merged and same_property(merged[ak], p):
            return merge_into(merged[ak], p)
        nk = name_key(p.name)
        if nk in by_name:
            cand = merged.get(by_name[nk])
            if cand is not None and same_property(cand, p):
                return merge_into(cand, p)
        # containment fallback: "Pavilion at The Groves" (RealPage) is the same
        # asset as "Pavilion at the Groves Apartment Homes" (CoStar). Only a
        # UNIQUE containment with no phase marker qualifies, and same_property()
        # still guards against merging distinct deals.
        toks = set(nk.split())
        cont = [k2 for k2 in by_name
                if k2 != nk and _containment_ok(toks, set(k2.split()))]
        if len(cont) == 1:
            cand = merged.get(by_name[cont[0]])
            if cand is not None and same_property(cand, p):
                return merge_into(cand, p)
        key = ak or ("name:" + nk)
        if key in merged:                     # address taken by a different property
            key = f"{key}|{nk}"
        merged[key] = p
        by_name.setdefault(nk, key)
        return p

    def merge_into(base: Prop, other: Prop):
        base.sources |= other.sources
        # Units: keep CoStar's; flag if they differ materially
        if other.units and base.units and other.units != base.units:
            lo, hi = sorted((base.units, other.units))
            if hi - lo >= 3:  # ignore +/-2 unit noise
                base.note(f"Units: CoStar {base.units if 'CoStar' in base.sources else hi} "
                          f"vs RealPage {other.units if 'RealPage' in other.sources else lo}")
        # Occupancy / rent: keep both sources' values for comparison.
        base.costar_occ = base.costar_occ if base.costar_occ is not None else other.costar_occ
        base.costar_rent = base.costar_rent if base.costar_rent is not None else other.costar_rent
        base.rp_occ = base.rp_occ if base.rp_occ is not None else other.rp_occ
        base.rp_rent = base.rp_rent if base.rp_rent is not None else other.rp_rent
        base.rp_asking = base.rp_asking if base.rp_asking is not None else other.rp_asking
        # Style / stories / owner / location backfill
        base.style = base.style or other.style
        base.stories = base.stories or other.stories
        base.owner = base.owner or other.owner
        base.city = base.city or other.city
        base.state = base.state or other.state
        base.zipcode = base.zipcode or other.zipcode
        base.lat = base.lat if base.lat is not None else other.lat
        base.lng = base.lng if base.lng is not None else other.lng
        # Year built conflict
        if other.year_built and base.year_built and other.year_built != base.year_built:
            base.note(f"Year built: {min(base.year_built, other.year_built)}/"
                      f"{max(base.year_built, other.year_built)}")
        base.year_built = base.year_built or other.year_built
        base.construction_begin = base.construction_begin or other.construction_begin
        # Carry both sources' lifecycle status (used by classify()).
        base.costar_status = base.costar_status or other.costar_status
        base.rp_status = base.rp_status or other.rp_status
        return base

    for p in costar:
        register(p)
    for p in realpage:
        register(p)
    return list(merged.values())


OCC_DIVERGENCE = 0.02   # >=2 pts occupancy gap between sources -> flag
RENT_DIVERGENCE = 0.05  # >=5% rent gap between sources -> flag


def resolve_occ_rent(p: Prop, occ_source: str, rent_source: str,
                     flag_divergence: bool = True):
    """Choose the displayed occupancy/rent by source priority; flag divergence.

    CoStar rent is *asking*; RealPage rent is *effective* — divergence on rent is
    expected and is surfaced rather than silently averaged. Divergence notes are
    only added for delivered assets (a partial-lease-up vs 0% gap on a
    not-yet-open building is noise, not signal).
    """
    prio = {"costar": (p.costar_occ, p.rp_occ), "realpage": (p.rp_occ, p.costar_occ)}
    p.occupancy = next((v for v in prio[occ_source] if v is not None), None)

    # Roster "Avg Mkt Rent" is an ASKING/market figure. CoStar asking is the
    # primary source; RealPage's only rent is *effective* (not asking), so it is
    # never used here — RealPage contributes only when its export carries an
    # asking column (p.rp_asking). 'average' blends the available asking values.
    co, rp = p.costar_rent, p.rp_asking
    if rent_source == "realpage":
        p.asking_rent = rp if rp is not None else co
    elif rent_source == "average":
        vals = [v for v in (co, rp) if v is not None]
        p.asking_rent = sum(vals) / len(vals) if vals else None
    else:  # costar (default)
        p.asking_rent = co if co is not None else rp
    p.eff_rent = p.rp_rent          # effective rent retained for the Recon log

    if not flag_divergence:
        return
    if p.costar_occ is not None and p.rp_occ is not None \
            and abs(p.costar_occ - p.rp_occ) >= OCC_DIVERGENCE:
        p.note(f"Occ: CoStar {p.costar_occ:.0%} vs RealPage {p.rp_occ:.0%}")
    if p.costar_rent and p.rp_rent \
            and abs(p.costar_rent - p.rp_rent) / max(p.costar_rent, p.rp_rent) >= RENT_DIVERGENCE:
        p.note(f"Rent: CoStar ask ${p.costar_rent:,.0f} vs "
               f"RealPage eff ${p.rp_rent:,.0f}")


def _existing_signal(p: Prop) -> bool:
    """Either source says the building physically exists / is delivered."""
    return (p.costar_status.lower() == "existing"
            or p.rp_status.lower() in ("stabilized", "lease-up", "lease up"))


def _uc_signal(p: Prop) -> bool:
    cs = p.costar_status.lower()
    rp = p.rp_status.lower()
    return ("under construction" in cs
            or rp in ("under construction", "under construction/lease-up"))


def _proposed_signal(p: Prop) -> bool:
    cs = p.costar_status.lower()
    rp = p.rp_status.lower()
    return cs == "proposed" or rp in ("pre-planned", "preplanned", "planned",
                                      "proposed")


def _is_pipeline(p: Prop) -> bool:
    """A forward-supply deal (under construction or proposed), not yet delivered."""
    return (_uc_signal(p) or _proposed_signal(p)) and not _existing_signal(p)


# --------------------------------------------------------------------------- #
# Delivery-quarter pinning + bucketing
# --------------------------------------------------------------------------- #
def pin_delivery(p: Prop, deliveries: dict):
    """Assign a delivery quarter to a *delivered* property.

    Match the property's unit count to the CoStar quarterly deliveries series
    within +/-1 year of its year-built. An exact unit match pins the quarter; with
    no exact match we keep the year only ("Q? <year>", quarter unknown) rather than
    guessing — guessed quarters are noise in a large market. Undated delivered
    deals can be quarter-stamped by the analyst via --pipeline-dates.
    """
    if not p.year_built or not p.units:
        if p.year_built:
            p.deliv_year = p.year_built
            p.est_delivery = f"Q? {p.year_built}"
        return
    # 1) Exact unit match within +/-1 year -> precise quarter.
    exact = [(y, q) for (y, q), u in deliveries.items()
             if abs(y - p.year_built) <= 1 and u == p.units]
    if exact:
        y, q = sorted(exact)[0]
        p.deliv_year, p.deliv_q = y, q
        p.est_delivery = fmt_quarter(y, q)
        return
    # 2) No exact match: pick the same-year quarter with the closest delivered
    #    count (estimated). Keeps the absorption table populated; flagged as est.
    same_year = [(q, u) for (y, q), u in deliveries.items()
                 if y == p.year_built and u > 0]
    if same_year:
        q, _ = min(same_year, key=lambda t: abs(t[1] - p.units))
        p.deliv_year, p.deliv_q = p.year_built, q
        p.est_delivery = fmt_quarter(p.year_built, q)
        p.note("Delivery quarter estimated")
        return
    # 3) Year known but no deliveries recorded that year -> year only.
    p.deliv_year = p.year_built
    p.est_delivery = f"Q? {p.year_built}"


_QLABEL = re.compile(r"Q([1-4])\s*'?(\d{2,4})|(\d{4})\s*Q([1-4])", re.I)


def parse_quarter_label(label: str) -> Optional[tuple[int, int]]:
    """Parse 'Q2 2028' or '2028 Q2' (or Q2'28) -> (year, quarter)."""
    if not label:
        return None
    m = _QLABEL.search(str(label).strip())
    if not m:
        return None
    if m.group(1):
        q = int(m.group(1)); y = int(m.group(2))
        if y < 100:
            y += 2000
    else:
        y = int(m.group(3)); q = int(m.group(4))
    return y, q


def load_pipeline_dates(path) -> dict:
    """Read analyst-supplied delivery dates for pipeline deals.

    CSV with headers: property, est_delivery[, units]. Returns
    {name_key: {"yq": (y,q), "units": int|None}}.
    """
    import csv
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            r = {(k or "").strip().lower(): (v or "").strip()
                 for k, v in row.items()}
            name = r.get("property")
            yq = parse_quarter_label(r.get("est_delivery", ""))
            if not name or not yq:
                continue
            out[name_key(name)] = {"yq": yq, "units": _int(r.get("units"))}
    return out


def apply_pipeline_dates(props: list[Prop], dates: dict):
    for p in props:
        info = dates.get(name_key(p.name))
        if not info:
            continue
        y, q = info["yq"]
        p.deliv_year, p.deliv_q = y, q
        p.est_delivery = fmt_quarter(y, q)
        if info["units"]:
            p.units = info["units"]
        p.note("Est. delivery set by analyst")


def emit_pipeline_template(props: list[Prop], path):
    """Write a CSV of undated pipeline deals for the analyst to fill in."""
    import csv
    # Forecast-relevant deals without a precise delivery quarter.
    undated = [p for p in props
               if p.deliv_q is None
               and p.bucket in ("LEASING UP", "UNDER CONSTRUCTION", "PROPOSED")]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["property", "est_delivery", "units", "bucket", "costar_year",
                    "# Fill est_delivery as 'Q2 2028'. Re-run with --pipeline-dates."])
        for p in sorted(undated, key=lambda x: (x.bucket, -(x.units or 0))):
            w.writerow([p.name, "", p.units or "", p.bucket, p.year_built or "", ""])
    return len(undated)


DILIGENCE_COLS = ["type", "property", "units", "est_delivery", "status",
                  "leasing_pace", "notes", "source"]


def emit_diligence_template(props: list[Prop], path):
    """Write a per-project research template (the SKILL.md research phase fills
    it). Lists every lease-up / UC / proposed deal to verify, plus a blank row to
    add shadow-supply sites (rezonings, entitled/vacant tracts, untracked deals)."""
    import csv
    targets = [p for p in props
               if p.bucket in ("LEASING UP", "UNDER CONSTRUCTION", "PROPOSED")]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(DILIGENCE_COLS)
        for p in sorted(targets, key=lambda x: (x.bucket, -(x.units or 0))):
            w.writerow(["pipeline", p.name, p.units or "", p.est_delivery or "", "",
                        "", f"(verify {p.bucket.lower()})", ""])
        w.writerow(["shadow", "<latent site / rezoning / land sale>", "", "", "",
                    "", "potential future supply not in CoStar/RealPage", ""])
    return len(targets)


def load_diligence(path):
    """Read a filled diligence CSV (DILIGENCE_COLS). Returns list of dict rows."""
    import csv
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            r = {(k or "").strip().lower(): (v or "").strip()
                 for k, v in row.items()}
            if r.get("property") and not r["property"].startswith("<"):
                rows.append(r)
    return rows


def apply_diligence(props: list[Prop], rows):
    """Fold researched delivery/unit corrections back into the pipeline props.

    A researched status that disqualifies a deal removes it from the competitive
    set entirely — whether it's dead (cancelled / withdrawn), not competitive
    rental product ("not multifamily": a church conversion or for-sale homes), or
    deliberately excluded by the analyst (e.g. "exclude — different submarket").
    The deal still appears on the Diligence sheet, so the exclusion is documented,
    not silent."""
    DROP_KEYS = ("cancel", "withdrawn", "dead", "not multifamily", "not multi-family",
                 "exclude", "different submarket", "out of submarket", "out-of-submarket",
                 "wrong submarket")
    by = {name_key(p.name): p for p in props}
    drop = []
    for r in rows:
        if r.get("type", "pipeline") != "pipeline":
            continue
        p = by.get(name_key(r["property"]))
        if not p:
            continue
        # Only the explicit `status` field drives a drop/reclassify — NOT the
        # free-text `notes`, which legitimately mentions other deals ("…excluded
        # below", "distinct from the out-of-submarket comp") and would otherwise
        # drop a valid pin by accident. Put the drop reason in status ("exclude -
        # …"). Classify on the LEADING segment only (the convention is
        # "<bucket> - <detail>"), so a negated phrase in the detail tail — e.g.
        # "proposed - entitled; not under construction" — is not misread as a
        # promotion to Under Construction.
        st = (r.get("status") or "").lower()
        head = st.split(" - ", 1)[0].strip() or st
        if any(k in head for k in DROP_KEYS):
            p.note(f"Diligence: {r.get('status') or 'removed'} — dropped from competitive set")
            drop.append(p)
            continue
        # A researched address (e.g. for a RealPage pipeline deal that carries no
        # street address) drives the Proximity geocode and the map marker.
        if r.get("address"):
            p.address = r["address"].strip()
            if r.get("city"):
                p.city = r["city"].strip()
            if r.get("state"):
                p.state = r["state"].strip()
            if r.get("zip"):
                p.zipcode = str(r["zip"]).strip()[:5]
        yq = parse_quarter_label(r.get("est_delivery", ""))
        if yq:
            p.deliv_year, p.deliv_q = yq
            p.est_delivery = fmt_quarter(*yq)
        if _int(r.get("units")):
            p.units = _int(r["units"])
        if st:
            p.note(f"Diligence: {r['status']}")
            # researched status corrects the auto-classification (leading
            # segment only — see `head` above)
            if any(k in head for k in ("under construction", "leasing", "delivered")) \
                    and p.bucket == "PROPOSED":
                p.bucket = "UNDER CONSTRUCTION"
            elif any(k in head for k in ("proposed", "permitted", "planned",
                                         "stall", "entitle")) \
                    and p.bucket == "UNDER CONSTRUCTION":
                p.bucket = "PROPOSED"
    if drop:
        dropped = {id(p) for p in drop}
        props[:] = [p for p in props if id(p) not in dropped]



def _find_row(ws, needle, col=1, maxr=60):
    needle = needle.lower()
    for r in range(1, maxr + 1):
        v = ws.cell(r, col).value
        if v and needle in str(v).lower():
            return r
    return None


def parse_intake_subject(path):
    """Subject monthly market rent / effective rent / occupancy from the RR-T12
    intake's 'Lease Trend' tab. Returns {(year, month): {mkt, eff, occ}}."""
    wb = openpyxl.load_workbook(path, data_only=True)
    if "Lease Trend" not in wb.sheetnames:
        return {}
    ws = wb["Lease Trend"]
    hdr_row = next((r for r in range(1, 30)
                    if str(ws.cell(r, 1).value or "").strip().lower().startswith("month")),
                   None)
    if not hdr_row:
        return {}
    mkt_row = _find_row(ws, "HD Market Rent")
    eff_row = _find_row(ws, "HD Effective Rent / unit") or _find_row(ws, "HD Effective Rent")
    occ_row = _find_row(ws, "Physical Occupancy")
    conc_row = _find_row(ws, "HD Concession %")
    out = {}
    for c in range(2, ws.max_column + 1):
        my = parse_month_year(ws.cell(hdr_row, c).value)
        if not my:
            continue
        rec = {}
        for key, rw in (("mkt", mkt_row), ("eff", eff_row), ("occ", occ_row),
                        ("conc", conc_row)):
            if rw:
                v = ws.cell(rw, c).value
                if isinstance(v, (int, float)):
                    rec[key] = v
        if rec:
            out[my] = rec
    return out


def parse_realpage_subject_rents(path, subject_name):
    """Subject quarterly asking/effective rent (and occupancy, when the export
    carries an Occupancy metric) from a RealPage per-property 10-yr export (wide
    format: Metric rows, Y####Q# columns). Returns {(year, q): {ask, eff[, occ]}}."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    hdr = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    qcols = {}
    for c, v in enumerate(hdr, 1):
        m = re.match(r"Y(\d{4})Q([1-4])", str(v or ""))
        if m:
            qcols[c] = (int(m.group(1)), int(m.group(2)))
    key = name_key(subject_name)
    out = {}
    for r in range(2, ws.max_row + 1):
        if name_key(str(ws.cell(r, 1).value or "")) != key:
            continue
        metric = str(ws.cell(r, 4).value or "").strip().lower()
        field = ("eff" if "effective" in metric else "ask" if "asking" in metric
                 else "occ" if "occup" in metric else None)
        if not field:
            continue
        for c, yq in qcols.items():
            v = _float(ws.cell(r, c).value)
            if v:
                if field == "occ" and v > 1.5:     # percent (95.7) -> fraction
                    v /= 100.0
                out.setdefault(yq, {}).setdefault(field, v)
    return out


def parse_costar_property_analytics(path):
    """Parse the CoStar PER-PROPERTY analytics export (grouped two-row header;
    one quarterly time-series block per building).

    Returns {building_name: {"series": {(y, q): {ask, eff, occ, conc,
    absorption, inv}}, "deliveries": [((y, q), units), ...]}}.

    This file is the AUTHORITATIVE delivery-quarter source: each building's
    `Deliveries Units` marks the exact quarter CoStar recorded its delivery —
    pinning from it makes the roster's TTM delivered-units tie to the overall
    5-mile deliveries series exactly (no more unit-count guessing). It also
    carries every building's quarterly occupancy (lease-up trajectories) and the
    subject's own rent history.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    row1 = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    row2 = [ws.cell(2, c).value for c in range(1, ws.max_column + 1)]
    hdr = {str(v or "").strip(): i for i, v in enumerate(row2, 1)}

    def grouped(group, sub):
        cur = None
        for i, (a, b) in enumerate(zip(row1, row2), 1):
            if a and str(a).strip():
                cur = str(a).strip()
            if cur == group and str(b or "").strip() == sub:
                return i
        return None

    nmc = hdr.get("Building Name") or hdr.get("Property Name")
    pc = hdr.get("Period")
    ask_c = grouped("Asking Rent", "Per Unit")
    eff_c = grouped("Effective Rent", "Per Unit")
    occ_c = grouped("Occupancy", "Percent")
    conc_c = grouped("Effective Rent", "Concessions %") or hdr.get("Concessions %")
    abs_c = grouped("Absorption", "Units")
    inv_c = grouped("Inventory", "Units")
    del_c = grouped("Deliveries", "Units")
    out = {}
    for r in range(3, ws.max_row + 1):
        nm = ws.cell(r, nmc).value if nmc else None
        if not nm:
            continue
        m = _QRE.search(str(ws.cell(r, pc).value)) if pc else None
        if not m:
            continue
        yq = (int(m.group(1)), int(m.group(2)))
        ent = out.setdefault(str(nm).strip(), {"series": {}, "deliveries": []})
        ent["series"][yq] = {
            "ask": _float(ws.cell(r, ask_c).value) if ask_c else None,
            "eff": _float(ws.cell(r, eff_c).value) if eff_c else None,
            "occ": _float(ws.cell(r, occ_c).value) if occ_c else None,
            "conc": _float(ws.cell(r, conc_c).value) if conc_c else None,
            "absorption": _float(ws.cell(r, abs_c).value) if abs_c else None,
            "inv": _int(ws.cell(r, inv_c).value) if inv_c else None,
        }
        d = _int(ws.cell(r, del_c).value) if del_c else None
        if d:
            ent["deliveries"].append((yq, d))
    for ent in out.values():
        ent["deliveries"].sort()
    return out


def parse_costar_subject_rents(path, subject_name):
    """Subject quarterly asking/effective rent (+occ/conc) from the CoStar
    per-property analytics export. Returns {(year, q): {ask, eff, occ, conc}}."""
    pp = parse_costar_property_analytics(path)
    match = make_name_matcher(pp.keys())(subject_name)
    return pp[match]["series"] if match else {}


_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
     "nov", "dec"], start=1)}


def parse_month_year(s):
    """Parse 'Nov 2023' / 'November 2023' -> (year, month) or None."""
    if not s:
        return None
    m = re.search(r"([A-Za-z]{3,})\s+(\d{4})", str(s))
    if not m:
        return None
    mon = _MONTHS.get(m.group(1)[:3].lower())
    if not mon:
        return None
    return int(m.group(2)), mon


CONSTRUCTION_MONTHS = 24   # typical build duration: begin -> delivery


def estimate_pipeline_delivery(p: Prop, as_of: tuple[int, int]):
    """Estimate a delivery quarter for an under-construction / proposed deal.

    Priority: (1) Construction Begin + ~24 months -> quarter; (2) CoStar Year
    Built (= expected completion year) at mid-year. Always pushed to land in the
    future (after the as-of quarter) so it enters the forward forecast.
    """
    est_idx = None
    my = parse_month_year(p.construction_begin)
    if my:
        y, mo = my
        mo += CONSTRUCTION_MONTHS
        y += (mo - 1) // 12
        mo = (mo - 1) % 12 + 1
        q = (mo - 1) // 3 + 1
        est_idx = quarter_index(y, q)
        # reconcile with CoStar completion year if it disagrees by >1 yr
        if p.year_built and abs(y - p.year_built) > 1:
            est_idx = quarter_index(p.year_built, q)
    elif p.year_built:
        est_idx = quarter_index(p.year_built, 2)
    if est_idx is None:
        return
    est_idx = max(est_idx, quarter_index(*as_of) + 1)
    p.deliv_year, p.deliv_q = est_idx // 4, est_idx % 4 + 1
    p.est_delivery = fmt_quarter(p.deliv_year, p.deliv_q)


def classify(p: Prop, as_of: tuple[int, int], target: float):
    """Assign one of the four lifecycle buckets, driven by source status.

    Precedence: a delivered/existing signal (from either source) wins over
    under-construction, which wins over proposed. Among delivered deals, occupancy
    and recency split stabilized vs leasing-up.
    """
    recent = bool(p.year_built and p.year_built >= as_of[0] - 2)
    # "Started" = construction has broken ground on/before the as-of quarter.
    my = parse_month_year(p.construction_begin)
    begin_idx = quarter_index(my[0], (my[1] - 1) // 3 + 1) if my else None
    started = begin_idx is not None and begin_idx <= quarter_index(*as_of)

    if _existing_signal(p):
        occ = p.occupancy
        if occ is None:
            p.bucket = "LEASING UP" if recent else "STABILIZED / STABILIZING"
        elif occ >= STABILIZED_OCC:
            p.bucket = "STABILIZED / STABILIZING"
        elif recent:
            p.bucket = "LEASING UP"
        else:
            p.bucket = "STABILIZED / STABILIZING"   # older underperformer
    elif _uc_signal(p) or started:
        # Under construction = a UC status from either source, OR ground already
        # broken (construction begin on/before as-of) even if a source lags.
        p.bucket = "UNDER CONSTRUCTION"
    elif _proposed_signal(p):
        p.bucket = "PROPOSED"
    elif p.deliv_q is not None:                      # exact delivery, no status
        p.bucket = "LEASING UP" if recent and (p.occupancy or 0) < STABILIZED_OCC \
            else "STABILIZED / STABILIZING"
    elif p.year_built and p.year_built > as_of[0]:
        p.bucket = "UNDER CONSTRUCTION"
    elif recent:
        p.bucket = "LEASING UP"
    else:
        p.bucket = "STABILIZED / STABILIZING"

    # Lease-ups are where rent/occ accuracy matters most -> flag for HelloData
    if p.bucket == "LEASING UP":
        p.note("Verify rent/occ w/ HelloData")
    # Pipeline assets carry no real rent/occ yet
    if p.bucket in ("UNDER CONSTRUCTION", "PROPOSED"):
        p.occupancy = None
        p.eff_rent = None
    if p.bucket == "PROPOSED" and "RealPage" in p.sources and "CoStar" not in p.sources:
        p.note("RealPage pipeline (not yet in CoStar)")
    if p.units and p.units < 50 and "CoStar" not in p.sources:
        p.note("RealPage only (sub-50 unit)")


def derive_type(p: Prop) -> str:
    style = (p.style or "").lower()
    if "town" in style or "town" in p.name.lower():
        return "Townhome"
    if "single" in style:
        return "Single Family"
    if style in ("podium", "wrap"):
        return "Mid-Rise"
    if style == "garden":
        # refine by stories
        if p.stories and p.stories >= 4:
            return "Mid-Rise"
        return "Garden"
    s = p.stories or 0
    if s >= 8:
        return "High-Rise"
    if s >= 4:
        return "Mid-Rise"
    if s == 3:
        return "Low-Rise"
    return "Garden"


# --------------------------------------------------------------------------- #
# Workbook writer
# --------------------------------------------------------------------------- #
BUCKET_ORDER = [
    ("STABILIZED / STABILIZING", "Stabilized / leasing-complete deliveries"),
    ("LEASING UP", "Recently delivered, still leasing"),
    ("UNDER CONSTRUCTION", "Under construction, not yet delivered"),
    ("PROPOSED", "Proposed / pre-planned pipeline"),
]

# Per-bucket section colours, carried over from the reference template:
# header band colour + a light matching row tint to distinguish each section.
BUCKET_STYLES = {
    "STABILIZED / STABILIZING": {"header": "FF2E75B6", "row": "FFDDEBF7"},  # blue
    "LEASING UP":               {"header": "FFED7D31", "row": "FFFCE4D6"},  # orange
    "UNDER CONSTRUCTION":       {"header": "FF375623", "row": "FFE2EFDA"},  # green
    "PROPOSED":                 {"header": "FFFF0000", "row": "FFFCE4E4"},  # red
}

COLS = {  # column letter -> (header, width)
    "B": ("#", 3.5),
    "C": ("Property", 30),
    "D": ("Units", 8),
    "E": ("Est. Delivery", 11.5),
    "F": ("Occupancy", 10),
    "G": ("Avg Mkt Rent", 13),
    "H": ("Owner", 22),
    "I": ("Proximity", 11),
    "J": ("Type", 14),
    "K": ("Notes", 30),
}


def hist_annual_absorption(series: dict, as_of: tuple[int, int], n_qtrs=12,
                           qtd=frozenset()):
    """Average annualized net absorption over the trailing n quarters (CoStar).
    Partial (QTD) quarters are excluded — a 10-day quarter would drag the
    average down."""
    as_idx = quarter_index(*as_of)
    vals = [rec["absorption"] for (y, q), rec in series.items()
            if 0 <= as_idx - quarter_index(y, q) < n_qtrs
            and rec.get("absorption") is not None and (y, q) not in qtd]
    if not vals:
        return 0
    return sum(vals) * 4 / len(vals)


def subject_annual_by_window(plan, as_idx, subj_monthly, subj_costar,
                             subj_realpage=None):
    """Aggregate subject rents/occupancy into each relative-year TTM window.

    HelloData (mix-weighted) is preferred; where it doesn't cover a window fall
    back to the CoStar or RealPage per-property series — whichever tracks HelloData
    more closely in the overlap (chosen per deal/market). Those fallback years show
    the **actual** source figures: Asking Rent -> the market-rent row, Effective
    Rent -> the effective-rent row (no scaling). Occupancy comes from the operating
    statements (T-12) as far back
    as they reach, then CoStar per-property occupancy, then RealPage's (when its
    export carries an occupancy metric). Returns {column_label:
    {mkt,eff,occ,conc,src}} and the chosen fallback source name.
    """
    out = {}
    subj_monthly = subj_monthly or {}
    subj_costar = subj_costar or {}
    subj_realpage = subj_realpage or {}

    def cal_year_avg(d, key, idxfn):
        agg = {}
        for k, rec in d.items():
            if rec.get(key) is not None:
                agg.setdefault(idxfn(k), []).append(rec[key])
        return {y: sum(v) / len(v) for y, v in agg.items()}
    hd_eff_y = cal_year_avg(subj_monthly, "eff", lambda k: k[0])

    def fit(src):
        sy = cal_year_avg(src, "eff", lambda k: k[0])
        common = [y for y in hd_eff_y if y in sy and sy[y]]
        if not common:
            return (float("inf"), 1.0)
        miss = sum(abs(hd_eff_y[y] - sy[y]) for y in common) / len(common)
        ratio = sum(hd_eff_y[y] / sy[y] for y in common) / len(common)
        return (miss, ratio)
    cs_fit, rp_fit = fit(subj_costar), fit(subj_realpage)
    # pick the better-tracking source for rents (CoStar wins ties / when no HD)
    if rp_fit[0] < cs_fit[0]:
        fb, ratio, fb_name = subj_realpage, rp_fit[1], "RealPage"
    else:
        fb, ratio, fb_name = subj_costar, cs_fit[1], "CoStar"

    for (label, kind, k) in plan:
        if kind != "hist":
            continue
        end_idx = as_idx - 4 * k
        ey, eq = end_idx // 4, end_idx % 4 + 1
        end_m = eq * 3
        months = []
        y, m = ey, end_m
        for _ in range(12):
            months.append((y, m))
            m -= 1
            if m == 0:
                m = 12; y -= 1
        hd = [subj_monthly[mm] for mm in months if mm in subj_monthly]
        def avg(recs, key):
            vals = [r[key] for r in recs if r.get(key) is not None]
            return sum(vals) / len(vals) if vals else None
        qs = [(yy, qq) for yy in (ey, ey - 1) for qq in (1, 2, 3, 4)
              if end_idx - 4 < quarter_index(yy, qq) <= end_idx]
        def srcavg(source, key):
            vals = [source[q][key] for q in qs
                    if q in source and source[q].get(key) is not None]
            return (sum(vals) / len(vals)) if vals else None

        def occ_fallback():
            # occupancy beyond the operating statements: CoStar per-property, then
            # RealPage per-property (used when its export carries an occupancy metric)
            v = srcavg(subj_costar, "occ")
            return v if v is not None else srcavg(subj_realpage, "occ")
        # HD drives the window when it covers most of it — or when it's the only
        # source with data (>=4 months beats an empty fallback).
        fb_has_rent = bool(srcavg(fb, "ask") or srcavg(fb, "eff"))
        if len(hd) >= 10 or (len(hd) >= 4 and not fb_has_rent):
            occ = avg(hd, "occ")
            if occ is None:                      # fill financials gap from CoStar
                occ = occ_fallback()
            out[label] = {"mkt": avg(hd, "mkt"), "eff": avg(hd, "eff"),
                          "occ": occ, "conc": avg(hd, "conc"),
                          "src": "HD" if len(hd) >= 10 else f"HD ({len(hd)} mo)"}
        else:
            ask = srcavg(fb, "ask")              # rents from the better-fit source
            eff = srcavg(fb, "eff")
            occ = avg(hd, "occ")                 # occupancy: financials, else CoStar/RealPage
            if occ is None:
                occ = occ_fallback()
            conc = avg(hd, "conc")
            if conc is None:
                conc = srcavg(subj_costar, "conc")
            if ask or eff or occ is not None:
                # Use the ACTUAL historical figures: CoStar/RealPage Asking Rent for
                # the market-rent row and Effective Rent for the effective-rent row.
                # (No level-alignment scaling — that distorted the real historical
                # rents; the market and effective rows must each show their own
                # source series.)
                out[label] = {"conc": conc, "occ": occ, "src": fb_name,
                              "mkt": ask, "eff": eff}
    return out, fb_name


def build_forecast_sheet(wb, series, props, as_of, target, latest_uc=None,
                         latest_label=None, subj_monthly=None, subj_costar=None,
                         subj_realpage=None, subject_name="", hist_years=6,
                         fwd_years=6, model_link=True,
                         model_sheet="Cash Flow (Annual)",
                         model_tp_sheet="Rent & Occ Data", close_quarter=None,
                         qtd=frozenset(), roster_rows=None,
                         subject_delivery=None):
    """Relative-year (trailing-12-month) supply / absorption / occupancy view.

    Columns are TTM windows: Y0 = the T12 ending at the as-of quarter, -Y1..-Yn
    step back a year each, Y1..Ym are the hold years anchored to an editable Close
    Quarter. Historical = CoStar actuals; forecast grows inventory by scheduled
    pipeline deliveries and occupied units by the Bear/Base/Bull annual demand.

    Y0 is LINKED, not hard-coded: its New Supply is a live SUMIFS over the
    Competitive Analysis roster's delivered units in the Y0 window (+ the subject
    if it delivered in-window), inventory/occupied roll forward from -Y1, and
    occupancy = occupied / inventory — so a re-pinned delivery quarter flows
    through supply AND occupancy. A partial Y0 (fewer than 4 complete quarters of
    CoStar data) shows ANNUALIZED absorption, labeled as such.
    """
    ws = wb.create_sheet("Supply & Absorption")
    ws.sheet_view.showGridLines = False
    NAVYF = font(bold=True, size=9, color=WHITE)
    EDIT = fill("FFFFF2CC")

    as_idx = quarter_index(*as_of)
    # Close (Y1 start): analyst-supplied --close, else default to as-of + 2 quarters.
    close_idx = quarter_index(*close_quarter) if close_quarter else as_idx + 2
    cy, cq = close_idx // 4, close_idx % 4 + 1

    # ----- precompute historical annual (TTM) actuals from CoStar -----
    def win_qtrs(end_idx):
        return [((end_idx - k) // 4, (end_idx - k) % 4 + 1) for k in range(4)]

    def win_sum(end_idx, key, complete_only=False):
        tot = 0; any_ = False
        for yq in win_qtrs(end_idx):
            if complete_only and yq in qtd:
                continue
            rec = series.get(yq)
            if rec and rec.get(key) is not None:
                tot += rec[key]; any_ = True
        return tot if any_ else None

    def win_complete(end_idx, key="absorption"):
        """# of complete (non-QTD) quarters in the window with data for `key`."""
        return sum(1 for yq in win_qtrs(end_idx)
                   if yq not in qtd and series.get(yq)
                   and series[yq].get(key) is not None)

    def at(end_idx, key):
        rec = series.get((end_idx // 4, end_idx % 4 + 1))
        return rec.get(key) if rec else None

    # relative-year column plan: list of (label, kind, k)
    plan = []
    for off in range(hist_years, -1, -1):          # -Y6 ... Y0
        plan.append((f"-Y{off}" if off else "Y0", "hist", off))
    for k in range(1, fwd_years + 1):              # Y1 ... Y6
        plan.append((f"Y{k}", "fcst", k))

    # ----- title -----
    ncols = len(plan)
    last_col = 2 + ncols                            # B=labels, C.. = years
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=last_col)
    t = ws.cell(2, 2, "SUPPLY & ABSORPTION  —  5-MILE MARKET (relative-year / TTM)")
    t.fill = fill(NAVY); t.font = font(bold=True, size=13, color=WHITE)
    t.alignment = CENTER
    ws.row_dimensions[2].height = 22

    # ----- assumptions (editable, yellow) -----
    base = round(hist_annual_absorption(series, as_of, qtd=qtd) / 25) * 25
    bear = max(0, round(base * 0.5 / 25) * 25)
    bull = round(base * 1.5 / 25) * 25
    A = [
        ("As-of Quarter (Y0 end)", fmt_quarter(*as_of), None, False,
         "Y0 = the trailing-12-months ending here (latest complete CoStar "
         "quarter); -Y1…-Y6 step back a year each."),
        ("Close Quarter (Y1 start)", fmt_quarter(cy, cq), None, True,
         "Expected deal close. Y1 = the 12 months starting here; pipeline "
         "deliveries bucket into hold years off this anchor — edit it and the "
         "Y1–Y6 windows & supply shift."),
        ("Stabilization Target", target, "0%", True, None),
        ("Demand Scenario", "Base", None, True, None),
        ("Bear Annual Absorption", bear, "#,##0", True, None),
        ("Base Annual Absorption", base, "#,##0", True, None),
        ("Bull Annual Absorption", bull, "#,##0", True,
         "Base = trailing-3-yr CoStar average (annualized, complete quarters)."),
        ("Selected Annual Demand",
         '=IF($C$7="Bear",$C$8,IF($C$7="Bull",$C$10,$C$9))', "#,##0", False, None),
    ]
    for i, (lab, val, fmt, editable, note) in enumerate(A, start=4):
        ws.cell(i, 2, lab).font = font(size=9, bold=True)
        c = ws.cell(i, 3, val)
        c.alignment = CENTER
        c.font = font(size=9, bold=True,
                      color=INPUT_BLUE if editable else "FF000000")
        if fmt:
            c.number_format = fmt
        if editable:
            c.fill = EDIT
        if note:
            nc = ws.cell(i, 4, "◂ " + note)
            nc.font = font(size=7, italic=True, color="FF808080")
            nc.alignment = LEFT
    dv = DataValidation(type="list", formula1='"Bear,Base,Bull"', allow_blank=False)
    ws.add_data_validation(dv); dv.add(ws["C7"])
    # numeric helpers in hidden column Z (asof / close index / selected rank)
    ws["Z1"] = as_idx
    ws["Z2"] = ('=IFERROR(VALUE(RIGHT($C$5,4))*4+'
                'MATCH(LEFT($C$5,2),{"Q1","Q2","Q3","Q4"},0)-1,0)')
    ws["Z3"] = '=IF($C$7="Bear",3,IF($C$7="Base",2,1))'
    ws.column_dimensions["Z"].hidden = True
    DEMAND = "$C$11"; TARGET = "$C$6"
    CLOSE = "$Z$2"; ASOF = "$Z$1"; SELRANK = "$Z$3"

    # ----- pipeline blocks (cols R:X) -----
    # (A) UNDER CONSTRUCTION — certain supply, LINKED from the Competitive
    #     Analysis roster (units & delivery date), counts in every scenario.
    # (B) PROPOSED — speculative; per-deal "Built In" scenario toggle so you can
    #     layer a deal into the Bear (downside / more-supply) case only.
    uc = [p for p in props if p.bucket == "UNDER CONSTRUCTION" and p.roster_row]
    prop = [p for p in props if p.bucket == "PROPOSED"]

    def piped_headers(row, title, cols):
        ws.cell(row - 1, 18, title).font = NAVYF
        ws.cell(row - 1, 18).fill = fill(NAVY)
        for j, lab in enumerate(cols):
            cc = ws.cell(row, 18 + j, lab)
            cc.fill = fill(BLUE); cc.font = font(bold=True, size=8, color=WHITE)
            cc.alignment = CENTER; cc.border = BORDER

    # Visible cols R(Property) S(Units) T(Est Delivery) U(Built In, proposed only);
    # hidden helper cols V(DelivIdx) W(HoldYr) X(Built?).
    DIDX = ('=IFERROR(VALUE(RIGHT(T{r},4))*4+'
            'MATCH(LEFT(T{r},2),{{"Q1","Q2","Q3","Q4"}},0)-1,"")')
    HYR = ('=IF(V{r}="","",IF(V{r}<=' + ASOF + ',0,'
           'MAX(1,INT((V{r}-' + CLOSE + ')/4)+1)))')

    # (A) UC block
    uc_hdr = 4
    piped_headers(uc_hdr, "UNDER CONSTRUCTION (linked from Competitive Analysis)",
                  ["Property", "Units", "Est. Delivery"])
    rr = uc_hdr + 1
    for p in sorted(uc, key=lambda x: -(x.units or 0)):
        rw = p.roster_row
        ws.cell(rr, 18, f"='Competitive Analysis'!C{rw}").font = font(size=9)
        ws.cell(rr, 19, f"='Competitive Analysis'!D{rw}").number_format = "#,##0"
        ws.cell(rr, 20, f"='Competitive Analysis'!E{rw}")
        ws.cell(rr, 22, DIDX.format(r=rr))
        ws.cell(rr, 23, HYR.format(r=rr))
        for col in range(18, 21):
            cc = ws.cell(rr, col); cc.border = BORDER
            cc.alignment = LEFT if col == 18 else CENTER
            if col == 18:
                cc.font = font(size=9)
        rr += 1
    ucf, ucl = uc_hdr + 1, max(uc_hdr + 1, rr - 1)
    UC_U = f"$S${ucf}:$S${ucl}"; UC_H = f"$W${ucf}:$W${ucl}"

    # (B) Proposed block
    pp_hdr = ucl + 3
    piped_headers(pp_hdr, "PROPOSED PIPELINE (scenario toggle)",
                  ["Property", "Units", "Est. Delivery", "Built In"])
    builtin_dv = DataValidation(
        type="list", formula1='"Bear only,Bear+Base,All,None"', allow_blank=True)
    ws.add_data_validation(builtin_dv)
    rr = pp_hdr + 1
    for p in sorted(prop, key=lambda x: -(x.units or 0)):
        est = p.est_delivery if (p.deliv_year and p.deliv_q) else ""
        ws.cell(rr, 18, p.name).font = font(size=9)
        ws.cell(rr, 19, p.units).number_format = "#,##0"
        ws.cell(rr, 20, est)
        ws.cell(rr, 21, "Bear only")                  # default: downside case only
        ws.cell(rr, 22, DIDX.format(r=rr))
        ws.cell(rr, 23, HYR.format(r=rr))
        # Built? per selected scenario (more-supply/Bear has the most deals)
        ws.cell(rr, 24, f'=IF(U{rr}="All",1,IF(U{rr}="Bear+Base",'
                        f'IF({SELRANK}>=2,1,0),IF(U{rr}="Bear only",'
                        f'IF({SELRANK}>=3,1,0),0)))')
        for col in range(18, 22):
            cc = ws.cell(rr, col); cc.border = BORDER
            cc.alignment = LEFT if col == 18 else CENTER
            if col == 18:
                cc.font = font(size=9)
        for col in (20, 21):
            cc = ws.cell(rr, col)
            cc.fill = EDIT; cc.font = font(size=9, color=INPUT_BLUE)
        builtin_dv.add(ws.cell(rr, 21))
        rr += 1
    ppf, ppl = pp_hdr + 1, max(pp_hdr + 1, rr - 1)
    PP_U = f"$S${ppf}:$S${ppl}"; PP_H = f"$W${ppf}:$W${ppl}"; PP_B = f"$X${ppf}:$X${ppl}"
    for hcol in ("V", "W", "X"):
        ws.column_dimensions[hcol].hidden = True

    # ----- subject annual series (HelloData -> CoStar, level-aligned) -----
    subj_annual, fb_name = subject_annual_by_window(
        plan, as_idx, subj_monthly, subj_costar, subj_realpage)

    # ----- annual table -----
    HR = 17                                    # relative-year header row
    ws.cell(HR, 2, "5-MILE MARKET").font = font(bold=True, size=9)
    rows = {"period": HR + 1, "supply": HR + 2, "absorp": HR + 3, "occ": HR + 4,
            "smkt": HR + 6, "smkt_yoy": HR + 7, "seff": HR + 8, "seff_yoy": HR + 9,
            "socc": HR + 10, "sconc": HR + 11, "_inv": HR + 13, "_occu": HR + 14}
    ws.cell(rows["supply"], 2, "NEW SUPPLY (5-mi)").font = font(size=9, bold=True)
    ws.cell(rows["absorp"], 2, "ABSORPTION (5-mi)").font = font(size=9, bold=True)
    ws.cell(rows["occ"], 2, "OCCUPANCY (5-mi)").font = font(size=9, bold=True)
    ws.cell(HR + 5, 2, "SUBJECT (" + (subject_name or "subject") + ")").font = font(bold=True, size=9)
    ws.cell(rows["smkt"], 2, f"  Market Rent  ({fb_name}→HD)").font = font(size=9, bold=True)
    ws.cell(rows["smkt_yoy"], 2, "    Market Rent YoY %").font = font(size=8, italic=True)
    ws.cell(rows["seff"], 2, "  Effective Rent").font = font(size=9, bold=True)
    ws.cell(rows["seff_yoy"], 2, "    Effective Rent YoY %").font = font(size=8, italic=True)
    ws.cell(rows["socc"], 2, "  Occupancy (financials / CoStar)").font = font(size=9, bold=True)
    ws.cell(rows["sconc"], 2, "  Concession %").font = font(size=9, bold=True)
    ws.cell(rows["_inv"], 2, "  inventory").font = font(size=8, color="FF808080")
    ws.cell(rows["_occu"], 2, "  occupied").font = font(size=8, color="FF808080")

    def L(ci):
        return get_column_letter(ci)

    # Cross-sheet ranges for the LINKED Y0 supply: the roster's delivered units
    # summed by delivery-quarter index (hidden col M on Competitive Analysis).
    CA_U = CA_M = None
    if roster_rows:
        rf, rl = roster_rows
        CA_U = f"'Competitive Analysis'!$D${rf}:$D${rl}"
        CA_M = f"'Competitive Analysis'!$M${rf}:$M${rl}"
    # Subject delivered units (added back when its delivery falls in a window —
    # CoStar's 5-mi series counts it, the competitive roster excludes it).
    subj_del_idx = subj_del_units = None
    if subject_delivery:
        (sdy, sdq), sdu = subject_delivery
        subj_del_idx, subj_del_units = quarter_index(sdy, sdq), (sdu or 0)

    partials = {}                      # label -> n complete quarters (if < 4)
    for j, (label, kind, k) in enumerate(plan):
        ci = 3 + j
        col = L(ci)
        # header band
        hc = ws.cell(HR, ci, label)
        hc.fill = fill(NAVY if kind == "hist" else BLUE)
        hc.font = NAVYF; hc.alignment = CENTER; hc.border = BORDER
        if kind == "hist":
            end_idx = as_idx - 4 * k
            sup = win_sum(end_idx, "deliveries")
            occ = at(end_idx, "occ_pct")
            inv = _int(at(end_idx, "inventory"))
            occu = _int(at(end_idx, "occ_units"))
            # absorption: complete quarters only; annualize a partial window
            ab_actual = win_sum(end_idx, "absorption", complete_only=True)
            n_comp = win_complete(end_idx)
            partial = ab_actual is not None and 0 < n_comp < 4
            ab = (round(ab_actual * 4 / n_comp) if partial else ab_actual)
            if partial:
                partials[label] = n_comp
            ey, eq = end_idx // 4, end_idx % 4 + 1
            sy, sq = (end_idx - 3) // 4, (end_idx - 3) % 4 + 1
            ws.cell(rows["period"], ci,
                    f"Q{sq}'{sy % 100:02d}-Q{eq}'{ey % 100:02d}"
                    + (f" ({n_comp}q ann.)" if partial else ""))
            if k == 0 and CA_U:
                # ---- Y0: LINKED to the Competitive Analysis roster ----
                prev = L(ci - 1)
                w_lo, w_hi = as_idx - 3, as_idx
                y0_sup = (f'=SUMIFS({CA_U},{CA_M},">="&{w_lo},{CA_M},"<="&{w_hi})')
                if subj_del_idx is not None and w_lo <= subj_del_idx <= w_hi:
                    y0_sup += f"+{subj_del_units}"
                ws.cell(rows["supply"], ci, y0_sup)
                prev_inv = _int(at(end_idx - 4, "inventory"))
                prev_occu = _int(at(end_idx - 4, "occ_units"))
                if prev_inv is not None and prev_occu is not None:
                    # inventory & occupied roll forward from -Y1, so occupancy
                    # responds to roster/absorption edits
                    ws.cell(rows["_inv"], ci,
                            f"={prev}{rows['_inv']}+{col}{rows['supply']}")
                    if partial:
                        # occupied grows by ACTUAL absorption (not annualized)
                        ws.cell(rows["absorp"], ci, ab)
                        ws.cell(rows["_occu"], ci,
                                f"={prev}{rows['_occu']}+{round(ab_actual)}")
                    else:
                        ws.cell(rows["absorp"], ci, ab)
                        ws.cell(rows["_occu"], ci,
                                f"={prev}{rows['_occu']}+{col}{rows['absorp']}")
                    ws.cell(rows["occ"], ci,
                            f'=IFERROR({col}{rows["_occu"]}/{col}{rows["_inv"]},"")')
                else:                         # no -Y1 anchor: static fallback
                    ws.cell(rows["absorp"], ci, ab)
                    ws.cell(rows["_inv"], ci, inv)
                    ws.cell(rows["_occu"], ci, occu)
                    ws.cell(rows["occ"], ci, occ)
            else:
                ws.cell(rows["supply"], ci, sup)
                ws.cell(rows["absorp"], ci, ab)
                ws.cell(rows["occ"], ci, occ)
                ws.cell(rows["_inv"], ci, inv)
                ws.cell(rows["_occu"], ci, occu)
            # subject rows (historical)
            srec = subj_annual.get(label)
            if srec:
                ws.cell(rows["smkt"], ci, round(srec["mkt"]) if srec.get("mkt") else None)
                ws.cell(rows["seff"], ci, round(srec["eff"]) if srec.get("eff") else None)
                ws.cell(rows["socc"], ci, srec.get("occ"))
        else:
            prev = L(ci - 1)
            # live window label anchored to the editable Close Quarter ($Z$2):
            # e.g. "Q1'27-Q4'27" — edit Close and the hold-year windows re-label
            s0, e0 = f"($Z$2+{4 * (k - 1)})", f"($Z$2+{4 * k - 1})"
            qlbl = ('="Q"&(MOD({s},4)+1)&"\'"&RIGHT(INT({s}/4),2)'
                    '&"-Q"&(MOD({e},4)+1)&"\'"&RIGHT(INT({e}/4),2)'
                    ).format(s=s0, e=e0)
            ws.cell(rows["period"], ci, qlbl)
            # New supply = UC (always) + proposed that are "built" this scenario
            ws.cell(rows["supply"], ci,
                    f"=SUMIFS({UC_U},{UC_H},{k})"
                    f"+SUMIFS({PP_U},{PP_H},{k},{PP_B},1)")
            ws.cell(rows["_inv"], ci,
                    f"={prev}{rows['_inv']}+{col}{rows['supply']}")
            ws.cell(rows["_occu"], ci,
                    f"=MIN({TARGET}*{col}{rows['_inv']},"
                    f"{prev}{rows['_occu']}+{DEMAND})")
            ws.cell(rows["absorp"], ci,
                    f"={col}{rows['_occu']}-{prev}{rows['_occu']}")
            ws.cell(rows["occ"], ci,
                    f"=IFERROR({col}{rows['_occu']}/{col}{rows['_inv']},0)")
        # formatting
        for rk in ("supply", "absorp", "_inv", "_occu"):
            cc = ws.cell(rows[rk], ci); cc.number_format = "#,##0"
            cc.alignment = CENTER; cc.font = font(size=9); cc.border = BORDER
        for rk in ("occ", "socc", "sconc"):
            oc = ws.cell(rows[rk], ci)
            oc.number_format = "0.0%"; oc.alignment = CENTER
            oc.font = font(size=9, bold=(rk == "occ")); oc.border = BORDER
        for rk in ("smkt_yoy", "seff_yoy"):
            yc = ws.cell(rows[rk], ci)
            yc.number_format = "0.0%"; yc.alignment = CENTER
            yc.font = font(size=8, italic=True, color="FF808080"); yc.border = BORDER
        for rk in ("smkt", "seff"):
            sc = ws.cell(rows[rk], ci)
            sc.number_format = '"$"#,##0'; sc.alignment = CENTER
            sc.font = font(size=9); sc.border = BORDER
        pc = ws.cell(rows["period"], ci)
        pc.font = font(size=8, color="FF808080"); pc.alignment = CENTER
        band = fill("FFF2F2F2" if kind == "hist" else "FFFFFFFF")
        for rk in ("supply", "absorp", "occ", "smkt", "smkt_yoy",
                   "seff", "seff_yoy", "socc", "sconc"):
            ws.cell(rows[rk], ci).fill = band
    # hide helper rows
    for rk in ("_inv", "_occu"):
        ws.row_dimensions[rows[rk]].hidden = True

    # ----- link the subject rows to the underwriting model (default) -----
    # Internal references to the TMG model's "Cash Flow (Annual)" tab, so when
    # these tabs are dragged into (or embedded in) the model they resolve to its
    # own projection: Y0 <- col F (T12/Y0), Y1..Y6 <- cols K..P; Market Rent <-
    # row 4, Effective Rent <- row 5, Occupancy <- row 14. Wrapped in IFERROR so
    # the standalone file shows a clean blank (Y1..Y6) or the chart's own value
    # (Y0 fallback) until the tab is carried into the model. Historical columns
    # (-Y6..-Y1) stay as the static RealPage/HelloData actuals.
    if model_link:
        link_rows = {"smkt": 4, "seff": 5, "socc": 14}
        chart_cols = [3 + hist_years + i for i in range(fwd_years + 1)]   # Y0,Y1..Y6
        model_cols = ["F"] + [get_column_letter(11 + k) for k in range(fwd_years)]  # F,K..P
        for rk, mrow in link_rows.items():
            for idx, (ci, mcol) in enumerate(zip(chart_cols, model_cols)):
                cell = ws.cell(rows[rk], ci)
                fb = cell.value if (idx == 0 and isinstance(cell.value, (int, float))) else None
                link = f"'{model_sheet}'!${mcol}${mrow}"
                cell.value = (f"=IFERROR({link},{fb})" if fb is not None
                              else f'=IFERROR({link},"")')

    # ----- subject derived rows (YoY % + concession %) — all columns -----
    # Written for every year (hist + forecast) so they populate wherever the
    # subject rent rows have data (static history, or the model links once in
    # the model). IFERROR keeps them blank when a year has no rent.
    for j in range(len(plan)):
        ci = 3 + j
        col = L(ci)
        ws.cell(rows["sconc"], ci,
                f'=IFERROR(({col}{rows["smkt"]}-{col}{rows["seff"]})/{col}{rows["smkt"]},"")')
        if j > 0:
            pcl = L(ci - 1)
            ws.cell(rows["smkt_yoy"], ci,
                    f'=IFERROR({col}{rows["smkt"]}/{pcl}{rows["smkt"]}-1,"")')
            ws.cell(rows["seff_yoy"], ci,
                    f'=IFERROR({col}{rows["seff"]}/{pcl}{rows["seff"]}-1,"")')

    fcst_cols = [3 + j for j, (_, kind, _) in enumerate(plan) if kind == "fcst"]
    y0_occu = f"${L(3 + hist_years)}${rows['_occu']}"   # actual occupied at Y0
    avg_ci = fcst_cols[-1] + 1                          # AVG column (one past Y6)
    cursor = rows["_occu"] + 2          # below the hidden inventory/occupied helpers

    # ----- 3rd-party market-rent-growth forecast vs TMG (model-linked) -----
    # Each shop's forward market-rent growth, pulled from the model's
    # 'Rent & Occ Data' tab (rows 31-34 = CoStar/RealPage/Yardi/GreenStreet,
    # cols C..H = Y1..Y6); TMG row = our own market-rent YoY. Primary read: does
    # OUR growth track the supply recovery above? Secondary: vs the consensus.
    def band_row(rrow, color):                          # fill B..AVG as one band
        for ci in range(2, avg_ci + 1):
            ws.cell(rrow, ci).fill = fill(color)

    if model_link:
        tp = cursor
        band_row(tp, NAVY)
        ws.cell(tp, 2, "MARKET-RENT GROWTH — TMG vs 3RD-PARTY FORECAST"
                ).font = font(bold=True, size=9, color=WHITE)
        for k, ci in enumerate(fcst_cols, start=1):
            hc = ws.cell(tp, ci, f"Y{k}"); hc.font = NAVYF; hc.alignment = CENTER
        ws.cell(tp, avg_ci, "AVG").font = NAVYF
        ws.cell(tp, avg_ci).alignment = CENTER

        sources = [("CoStar", 31), ("RealPage", 32), ("Yardi", 33), ("GreenStreet", 34)]
        src_first = tp + 1

        def growth_row(rrow, label, cells, color, bold):
            band_row(rrow, color)
            lc = ws.cell(rrow, 2, "  " + label)
            lc.font = font(size=9, bold=bold, color=NAVY if color == GOLD else "FF000000")
            for ci in fcst_cols + [avg_ci]:
                cc = ws.cell(rrow, ci, cells(ci))
                cc.number_format = "0.0%"; cc.alignment = CENTER
                cc.font = font(size=9, bold=bold); cc.border = BORDER

        for s_off, (lab, mrow) in enumerate(sources):
            def src_cell(ci, mrow=mrow):
                if ci == avg_ci:
                    return (f'=IFERROR(AVERAGE({L(fcst_cols[0])}{src_first+s_off}'
                            f':{L(fcst_cols[-1])}{src_first+s_off}),"")')
                return f"=IFERROR('{model_tp_sheet}'!${get_column_letter(3+fcst_cols.index(ci))}${mrow},\"\")"
            growth_row(src_first + s_off, lab, src_cell, GRAY, False)
        src_last = src_first + len(sources) - 1

        cons = src_last + 1                            # 4-source consensus
        growth_row(cons, "Consensus (4-source avg)",
                   lambda ci: f'=IFERROR(AVERAGE({L(ci)}{src_first}:{L(ci)}{src_last}),"")',
                   STEEL, True)

        tmg = cons + 1                                 # OUR growth — the focus
        myoy = rows["smkt_yoy"]
        growth_row(tmg, "TMG — our market-rent growth  ◄",
                   lambda ci: (f'=IFERROR(AVERAGE({L(fcst_cols[0])}{tmg}:{L(fcst_cols[-1])}{tmg}),"")'
                               if ci == avg_ci else f'=IFERROR({L(ci)}{myoy},"")'),
                   GOLD, True)
        cursor = tmg + 2                               # gap before scenario group

    # ----- collapsed group: Bear/Base/Bull scenario inputs -----
    sc_hdr = cursor
    ws.cell(sc_hdr, 2, "▸ SCENARIO INPUTS — Bear / Base / Bull  (implied occupancy, "
            "rent-growth & concession assumptions — click + to expand)"
            ).font = font(bold=True, size=8, color="FF595959")
    sb = sc_hdr + 1
    ws.cell(sb, 2, "IMPLIED 5-MI OCCUPANCY BY DEMAND SCENARIO").font = font(bold=True, size=9)
    for r_off, (sc_lab, abs_cell) in enumerate(
            [("Bear", "$C$8"), ("Base", "$C$9"), ("Bull", "$C$10")], start=1):
        rrow = sb + r_off
        lc = ws.cell(rrow, 2, sc_lab); lc.font = font(size=9, bold=True)
        for k, ci in enumerate(fcst_cols, start=1):
            col = L(ci)
            cc = ws.cell(rrow, ci,
                         f"=MIN({TARGET},({y0_occu}+{abs_cell}*{k})/{col}{rows['_inv']})")
            cc.number_format = "0.0%"; cc.alignment = CENTER; cc.font = font(size=9)
            cc.border = BORDER
        if r_off == 1:
            for k, ci in enumerate(fcst_cols, start=1):
                hc = ws.cell(sb, ci, f"Y{k}")
                hc.font = NAVYF; hc.fill = fill(BLUE); hc.alignment = CENTER

    # ----- rent-growth scenarios (editable assumptions) -----
    rg = sb + 5
    ws.cell(rg, 2, "MARKET RENT GROWTH (editable assumptions)").font = font(bold=True, size=9)
    base_g = [0.01, 0.03, 0.04, 0.05, 0.04, 0.03]
    conc_b = [0.03, 0.015, 0.005, 0.005, 0.005, 0.005]
    for k, ci in enumerate(fcst_cols, start=1):
        ws.cell(rg, ci, f"Y{k}").font = font(bold=True, size=8)
    growth_rows = {}
    for r_off, sc in enumerate(["Bear", "Base", "Bull"], start=1):
        rrow = rg + r_off
        ws.cell(rrow, 2, sc).font = font(size=9, bold=True)
        growth_rows[sc] = rrow
        for k, ci in enumerate(fcst_cols):
            g = base_g[k] + (-0.0125 if sc == "Bear" else 0.01 if sc == "Bull" else 0)
            cc = ws.cell(rrow, ci, round(g, 4))
            cc.number_format = "0.0%"; cc.alignment = CENTER
            cc.font = font(size=9, color=INPUT_BLUE)
            cc.fill = EDIT; cc.border = BORDER

    cg = rg + 4
    ws.cell(cg, 2, "CONCESSIONS % — forward assumption (editable)").font = font(bold=True, size=9)
    conc_rows = {}
    for r_off, sc in enumerate(["Bear", "Base", "Bull"], start=1):
        rrow = cg + r_off
        ws.cell(rrow, 2, sc).font = font(size=9, bold=True)
        conc_rows[sc] = rrow
        for k, ci in enumerate(fcst_cols):
            c = conc_b[k] + (0.03 if sc == "Bear" else -0.01 if sc == "Bull" else 0)
            c = max(c, 0)
            cc = ws.cell(rrow, ci, round(c, 4))
            cc.number_format = "0.0%"; cc.alignment = CENTER
            cc.font = font(size=9, color=INPUT_BLUE)
            cc.fill = EDIT; cc.border = BORDER

    eg = cg + 4
    ws.cell(eg, 2, "EFFECTIVE RENT GROWTH (derived)").font = font(bold=True, size=9)
    for r_off, sc in enumerate(["Bear", "Base", "Bull"], start=1):
        rrow = eg + r_off
        ws.cell(rrow, 2, sc).font = font(size=9, bold=True)
        for k, ci in enumerate(fcst_cols):
            col = L(ci)
            gr = f"{col}{growth_rows[sc]}"
            ct = f"{col}{conc_rows[sc]}"
            cp = f"{L(ci-1)}{conc_rows[sc]}" if k > 0 else None
            if k == 0:
                f = f"=(1+{gr})*(1-{ct})-1"
            else:
                f = f"=(1+{gr})*(1-{ct})/(1-{cp})-1"
            cc = ws.cell(rrow, ci, f)
            cc.number_format = "0.0%"; cc.alignment = CENTER; cc.font = font(size=9)
            cc.border = BORDER

    # collapse the whole Bear/Base/Bull scenario block under its summary header
    for grow in range(sb, eg + 4):
        ws.row_dimensions[grow].outlineLevel = 1
        ws.row_dimensions[grow].hidden = True

    # ----- collapsed: subject rent source by year + reconciliation -----
    sg = eg + 5
    ws.cell(sg, 2, "▸ DETAIL: subject rent source by year, delivered-units "
                   "tie-out & reconciliation (grouped — click + to expand)"
            ).font = font(bold=True, size=8)
    grp_first = sg + 1
    r = grp_first
    for (label, kind, k) in plan:
        if kind != "hist":
            continue
        srec = subj_annual.get(label)
        src = srec.get("src") if srec else "—"
        end_idx = as_idx - 4 * k
        ws.cell(r, 2, f"  {label}  "
                f"{fmt_quarter((end_idx-3)//4,(end_idx-3)%4+1)}–"
                f"{fmt_quarter(end_idx//4,end_idx%4+1)}").font = font(size=8)
        ws.cell(r, 5, src).font = font(size=8)
        r += 1
    uc_total = sum(p.units or 0 for p in uc)
    ws.cell(r, 2, "  UC scheduled vs CoStar UC").font = font(size=8)
    ws.cell(r, 5, f"{uc_total:,} / {latest_uc:,}" if latest_uc else f"{uc_total:,}").font = font(size=8)
    r += 1
    # Delivered-units tie-out: roster (+subject add-back) vs CoStar 5-mi series,
    # per historical TTM window. Y0's residual should be ~0 (sub-50 aside) — the
    # New Supply row above reads the ROSTER, this line audits it against CoStar.
    tie = delivery_tieout(props, series, as_of, lookback=min(4, hist_years),
                          subject_delivery=subject_delivery)
    if tie:
        ws.cell(r, 2, "  Delivered units — roster vs CoStar 5-mi series:"
                ).font = font(size=8, bold=True)
        r += 1
        for t in tie:
            lab = f"-Y{t['k']}" if t["k"] else "Y0"
            subj_txt = f" + subj {t['subject']:,}" if t["subject"] else ""
            rp_txt = (f"; roster also carries +{t['rp_only']:,} RealPage-only "
                      f"supply CoStar misses" if t["rp_only"] else "")
            gap = t["gap"]
            gap_txt = ("tie ✓" if abs(gap) < 5 else
                       f"+{gap:,.0f} sub-50/unnamed" if gap > 0 else
                       f"roster over by {-gap:,.0f} — check pins")
            ws.cell(r, 2, f"    {lab}: roster (CoStar-tracked) {t['roster_cs']:,}"
                          f"{subj_txt} vs CoStar {t['costar']:,.0f}   "
                          f"({gap_txt}{rp_txt})"
                    ).font = font(size=8,
                                  color="FF808080" if abs(gap) < 50 else "FFC00000")
            r += 1
    for label, n_comp in partials.items():
        ws.cell(r, 2, f"  {label} has only {n_comp} complete quarter(s) of CoStar "
                      f"data — its absorption is shown ANNUALIZED (×4/{n_comp}); "
                      f"occupancy uses actuals.").font = font(size=8, color="FF808080")
        r += 1
    if latest_label and "QTD" in str(latest_label):
        tail = ("the Y0 window includes it, so Y0 sums are annualized above."
                if as_of in qtd else
                "Y0 anchors to the latest complete quarter.")
        ws.cell(r, 2, f"  Newest CoStar row ({latest_label}) is partial (QTD) — "
                      f"excluded from TTM sums; {tail}"
                ).font = font(size=8, color="FF808080")
        r += 1
    for gr in range(grp_first, r):
        ws.row_dimensions[gr].outlineLevel = 1
        ws.row_dimensions[gr].hidden = True
    ws.sheet_properties.outlinePr.summaryBelow = False

    # ----- column widths + compact row heights -----
    ws.column_dimensions["A"].width = 2.5
    ws.column_dimensions["B"].width = 26
    for ci in range(3, last_col + 1):
        ws.column_dimensions[L(ci)].width = 9.5
    ws.column_dimensions[L(last_col + 1)].width = 9.5   # AVG column (P)
    for cw, w in {"R": 28, "S": 7, "T": 11, "U": 9, "V": 8, "W": 7, "X": 6}.items():
        ws.column_dimensions[cw].width = w
    for rr2 in range(1, r + 2):
        ws.row_dimensions[rr2].height = 14.4
    ws.row_dimensions[2].height = 20            # title
    return ws

def write_workbook(props, subject_name, latest_inv, latest_label,
                   as_of, target, out_path, series=None, latest_uc=None,
                   subj_monthly=None, subj_costar=None, subj_realpage=None,
                   diligence_rows=None, model_link=True,
                   model_sheet="Cash Flow (Annual)", close_quarter=None,
                   qtd=frozenset(), subject_delivery=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Competitive Analysis"
    ws.sheet_view.showGridLines = False

    for col, (_, width) in COLS.items():
        ws.column_dimensions[col].width = width
    ws.column_dimensions["A"].width = 3

    # ---- Title / subtitle ----
    ws.merge_cells("C2:G2")
    t = ws["C2"]
    t.value = f"{subject_name.upper()} — 5-Mile Competitive Supply"
    t.fill = fill(NAVY); t.font = font(bold=True, size=13, color=WHITE)
    t.alignment = CENTER
    ws.row_dimensions[2].height = 22

    delivered_years = sorted({p.deliv_year for p in props if p.deliv_year})
    yr_lo = delivered_years[0] if delivered_years else as_of[0]
    ws.merge_cells("B3:G3")
    s = ws["B3"]
    s.value = (f"{yr_lo}–{as_of[0]} New Construction  |  5-mile radius  |  "
               f"As of {latest_label}")
    s.fill = fill(BLUE); s.font = font(size=9, color=WHITE); s.alignment = LEFT

    # ---- Header row 4 ----
    hr = 4
    for col, (label, _) in COLS.items():
        c = ws[f"{col}{hr}"]
        c.value = label
        c.fill = fill(NAVY); c.font = font(bold=True, size=9, color=WHITE)
        c.alignment = CENTER; c.border = BORDER
    ws.row_dimensions[hr].height = 18

    # ---- Buckets ----
    r = hr + 1
    idx = 0
    for bucket, _desc in BUCKET_ORDER:
        members = [p for p in props if p.bucket == bucket]
        if not members:
            continue
        # chronological within each section: earliest delivery first, undated last
        members.sort(key=lambda p: (p_qi(p) if (p.deliv_year and p.deliv_q) else 10**9,
                                    -(p.units or 0)))
        tot_u = sum(p.units or 0 for p in members)
        hdr_color = BUCKET_STYLES[bucket]["header"]
        row_color = BUCKET_STYLES[bucket]["row"]
        # section header
        ws.merge_cells(f"C{r}:K{r}")
        sc = ws[f"C{r}"]
        sc.value = f"{bucket} ({len(members)} properties, {tot_u:,} units)"
        sc.fill = fill(hdr_color); sc.font = font(bold=True, size=9, color=WHITE)
        sc.alignment = LEFT
        ws[f"B{r}"].fill = fill(hdr_color)
        r += 1
        for p in members:
            idx += 1
            p.roster_row = r          # remember for cross-sheet links
            row_vals = {
                "B": idx,
                "C": p.name,
                "D": p.units,
                "E": p.est_delivery or "TBD",
                "F": p.occupancy,
                "G": p.asking_rent if p.asking_rent else "—",
                "H": p.owner or "—",
                "I": (round(p.proximity_mi, 1)
                      if p.proximity_mi is not None else None),
                "J": p.prop_type,
                "K": "; ".join(p.notes) if p.notes else None,
            }
            for col, val in row_vals.items():
                c = ws[f"{col}{r}"]
                c.value = val
                c.fill = fill(row_color); c.font = font(size=9)
                c.border = BORDER
                c.alignment = LEFT if col in ("C", "H", "K") else CENTER
            ws[f"D{r}"].number_format = "#,##0"
            ws[f"F{r}"].number_format = "0.0%"
            ws[f"G{r}"].number_format = '"$"#,##0;;"—"'
            ws[f"I{r}"].number_format = '0.0" mi";;"—"'
            # hidden helper: the row's delivery-quarter index (year*4+q-1) parsed
            # live from the Est. Delivery cell, so the Supply & Absorption tab can
            # SUMIFS the roster's delivered units per TTM window — the Y0 supply
            # figure stays LINKED to this roster ("TBD"/"Q? 2020" -> blank).
            ws[f"M{r}"] = (f'=IFERROR(VALUE(RIGHT(E{r},4))*4'
                           f'+MATCH(LEFT(E{r},2),{{"Q1","Q2","Q3","Q4"}},0)-1,"")')
            r += 1
        r += 1  # spacer
    ws.column_dimensions["M"].hidden = True
    roster_rows = (hr + 1, max(hr + 1, r - 2))   # data span for cross-sheet SUMIFS

    # ---- Pointer note (forward forecast lives on its own tab) ----
    note_r = r + 1
    ws.merge_cells(f"B{note_r}:K{note_r}")
    any_hd = any(p.hd_ask or p.hd_eff for p in props)
    rent_note = ("Rent ($) = HelloData mix-weighted asking where covered, else "
                 "market asking (CoStar)." if any_hd else "Rent ($) = market asking.")
    ws[f"B{note_r}"] = (f"* 5-Mile radius. {rent_note} Proximity (mi) = "
                        "straight-line distance from the subject. Est. Delivery "
                        "drives the Supply & Absorption tab's per-window supply "
                        "(edit it there or here — they are linked). See the 'Supply "
                        "& Absorption' tab for the forward supply / absorption / "
                        "overall-occupancy forecast.")
    ws[f"B{note_r}"].font = font(size=8, color="FF808080")

    # ---- Reconciliation log sheet ----
    rlog = wb.create_sheet("Reconciliation Log")
    rlog.append(["Property", "Address", "Units", "Year Built", "Est. Delivery",
                 "Deliv. Source", "Bucket", "CoStar Occ", "RealPage Occ", "HD Occ",
                 "CoStar Ask Rent", "RealPage Eff Rent", "HD Ask (mix-wtd)",
                 "HD Eff (mix-wtd)", "Sources", "Notes"])
    for c in rlog[1]:
        c.font = font(bold=True, color=WHITE); c.fill = fill(NAVY)
        c.alignment = CENTER
    ordered = sorted(props, key=lambda x: (BUCKET_ORDER.index(
        next(b for b in BUCKET_ORDER if b[0] == x.bucket)), -p_qi(x)))
    for p in ordered:
        rlog.append([p.name, p.address, p.units, p.year_built,
                     p.est_delivery, p.deliv_src, p.bucket,
                     p.costar_occ, p.rp_occ, p.hd_occ,
                     p.costar_rent, p.rp_rent, p.hd_ask, p.hd_eff,
                     "+".join(sorted(p.sources)), "; ".join(p.notes)])
    for i in range(2, len(ordered) + 2):
        for col in ("H", "I", "J"):
            rlog[f"{col}{i}"].number_format = "0.0%"
        for col in ("K", "L", "M", "N"):
            rlog[f"{col}{i}"].number_format = "#,##0"
    for col in "ABCDEFGHIJKLMNOP":
        rlog.column_dimensions[col].width = 15
    rlog.column_dimensions["A"].width = 30
    rlog.column_dimensions["B"].width = 24
    rlog.column_dimensions["P"].width = 44

    # ---- Forward supply / absorption / occupancy forecast ----
    if series:
        sa = build_forecast_sheet(wb, series, props, as_of, target, latest_uc=latest_uc,
                                  latest_label=latest_label, subj_monthly=subj_monthly,
                                  subj_costar=subj_costar, subj_realpage=subj_realpage,
                                  subject_name=subject_name, model_link=model_link,
                                  model_sheet=model_sheet, close_quarter=close_quarter,
                                  qtd=qtd, roster_rows=roster_rows,
                                  subject_delivery=subject_delivery)
        # make "Supply & Absorption" the 2nd tab
        wb.move_sheet(sa, -(wb.index(sa) - 1))

    if diligence_rows:
        write_diligence_sheet(wb, diligence_rows)

    wb.save(out_path)


def write_diligence_sheet(wb, rows):
    """Render researched per-project diligence + a shadow-supply watch list."""
    ws = wb.create_sheet("Diligence")
    ws.sheet_view.showGridLines = False
    headers = ["Property / Site", "Units", "Est. Delivery", "Status",
               "Leasing Pace", "Notes", "Source"]
    widths = [30, 8, 12, 16, 14, 50, 36]
    for sect, kind in (("PIPELINE DILIGENCE", "pipeline"),
                       ("SHADOW SUPPLY (latent / untracked — watch list)", "shadow")):
        srows = [r for r in rows if r.get("type", "pipeline") == kind]
        if not srows:
            continue
        r0 = (ws.max_row + 2) if ws.max_row > 1 else 2
        ws.merge_cells(start_row=r0, start_column=2, end_row=r0, end_column=8)
        sc = ws.cell(r0, 2, sect)
        sc.fill = fill(NAVY); sc.font = font(bold=True, size=11, color=WHITE)
        for j, h in enumerate(headers):
            c = ws.cell(r0 + 1, 2 + j, h)
            c.fill = fill(BLUE); c.font = font(bold=True, size=9, color=WHITE)
            c.alignment = CENTER; c.border = BORDER
        for i, r in enumerate(srows):
            rr = r0 + 2 + i
            vals = [r.get("property"), r.get("units"), r.get("est_delivery"),
                    r.get("status"), r.get("leasing_pace"), r.get("notes"),
                    r.get("source")]
            for j, v in enumerate(vals):
                c = ws.cell(rr, 2 + j, v or None)
                c.font = font(size=9); c.border = BORDER
                c.alignment = LEFT if j in (0, 3, 4, 5, 6) else CENTER
    for j, w in enumerate(widths):
        ws.column_dimensions[get_column_letter(2 + j)].width = w
    ws.column_dimensions["A"].width = 2.5
    return ws



def p_qi(p):
    return quarter_index(p.deliv_year, p.deliv_q) if p.deliv_year and p.deliv_q else -1


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_as_of(label: str) -> tuple[int, int]:
    """Parse an analysis-quarter label — both '2026 Q2' and 'Q2 2026' forms."""
    yq = parse_quarter_label(label or "")
    if yq:
        return yq
    today = dt.date.today()
    return today.year, (today.month - 1) // 3 + 1


def pin_delivery_from_property_analytics(p: Prop, pp: dict, pp_match) -> bool:
    """Pin the delivery quarter from the CoStar per-property analytics (the
    authoritative per-building `Deliveries Units` series). Returns True if
    pinned. A building delivering across several quarters is pinned to its
    largest delivery event (and noted)."""
    nm = pp_match(p.name) if pp else None
    if not nm:
        return False
    events = pp[nm]["deliveries"]
    if not events:
        return False
    (y, q), u = max(events, key=lambda t: t[1])
    p.deliv_year, p.deliv_q = y, q
    p.est_delivery = fmt_quarter(y, q)
    p.deliv_src = "CoStar property analytics"
    if len(events) > 1:
        p.note("Delivered across " + ", ".join(
            f"{fmt_quarter(*yq)} ({uu}u)" for yq, uu in events))
    return True


def apply_hellodata_stats(p: Prop, stats: dict):
    """Fold a property's HelloData stats into its roster row: mix-weighted
    asking/effective rent become the displayed rent (HD is the highest-fidelity
    rent source when it covers a comp), and lease-ups get an occupancy /
    leasing-pace read instead of a "verify manually" flag."""
    if not stats:
        return
    p.hd_ask, p.hd_eff = stats.get("ask"), stats.get("eff")
    p.hd_occ, p.hd_pace = stats.get("occ"), stats.get("pace")
    if p.bucket in ("UNDER CONSTRUCTION", "PROPOSED"):
        return
    if p.hd_ask:
        if p.asking_rent and abs(p.asking_rent - p.hd_ask) / p.hd_ask >= RENT_DIVERGENCE:
            p.note(f"Rent: HD mix-wtd ${p.hd_ask:,.0f} vs CoStar ask ${p.asking_rent:,.0f}")
        p.asking_rent = p.hd_ask
    if p.hd_eff:
        p.eff_rent = p.hd_eff
    if p.bucket == "LEASING UP":
        # replace the "verify w/ HelloData" flag with the actual HD read; the
        # HD cumulative-lease-up occupancy is the most credible figure for a
        # property still leasing (vendor occ is often stale), so display it
        if p.hd_occ is not None:
            if p.occupancy is not None and abs(p.hd_occ - p.occupancy) >= 0.05:
                p.note(f"Occ: HD ~{p.hd_occ:.0%} (CoStar/RP showed {p.occupancy:.0%})")
            p.occupancy = p.hd_occ
        p.notes[:] = [n for n in p.notes if "Verify rent/occ" not in n]
        bits = []
        if p.hd_occ is not None:
            bits.append(f"occ ~{p.hd_occ:.0%} (units leased)")
        if p.hd_pace is not None:
            bits.append(f"~{p.hd_pace:.0f} leases/mo")
        if bits:
            p.note("HD (90d): " + ", ".join(bits))
    elif p.occupancy is None and p.hd_occ is not None:
        p.occupancy = p.hd_occ


def build_competitive_roster(costar_roster_path, realpage_path, deliveries, as_of,
                             subject_name, subject_address, target=0.95,
                             occ_source="costar", rent_source="costar",
                             pp=None, hd_by_prop=None):
    """Parse + reconcile + classify the competitive new-construction roster.

    Shared by the chart and the map. Returns the kept Prop list (subject excluded,
    bucketed, with delivery quarters pinned/estimated). `pp` (the CoStar
    per-property analytics dict) makes delivery pinning authoritative and fills
    occupancy gaps; `hd_by_prop` (HelloData rows keyed by normalized name) drives
    mix-weighted comp rents and the lease-up occupancy read."""
    import subject_intake
    props = reconcile(parse_costar_roster(costar_roster_path),
                      parse_realpage(realpage_path))
    subj_addr = addr_key(subject_address)
    subj_name = name_key(subject_name)
    props = [p for p in props
             if not ((subj_addr and addr_key(p.address) == subj_addr)
                     or name_key(p.name) == subj_name)]
    pp_match = make_name_matcher(pp.keys()) if pp else (lambda n: None)
    hd_match = make_name_matcher(hd_by_prop.keys()) if hd_by_prop else (lambda n: None)
    keep = []
    for p in props:
        delivered = _existing_signal(p)
        if delivered:
            if not pin_delivery_from_property_analytics(p, pp, pp_match):
                pin_delivery(p, deliveries)
        else:
            estimate_pipeline_delivery(p, as_of)
        resolve_occ_rent(p, occ_source, rent_source, flag_divergence=delivered)
        # per-property analytics: fill an occupancy gap from the building's own
        # latest quarterly occupancy (e.g. a v1 roster with no Vacancy % column)
        nm = pp_match(p.name)
        if nm and p.occupancy is None and delivered:
            ser = pp[nm]["series"]
            latest = max((yq for yq, rec in ser.items()
                          if rec.get("occ") is not None), default=None)
            if latest:
                p.occupancy = ser[latest]["occ"]
        classify(p, as_of, target)
        p.prop_type = derive_type(p)
        hd_nm = hd_match(p.name)
        if hd_nm:
            apply_hellodata_stats(
                p, subject_intake.hellodata_property_stats(
                    hd_by_prop[hd_nm], total_units=p.units,
                    lease_up=(p.bucket == "LEASING UP")))
        if delivered and "CoStar" not in p.sources:
            p.note("RealPage-only — not in CoStar's 5-mi series")
        within_lookback = (p.year_built and
                           p.year_built >= as_of[0] - NEW_CONSTRUCTION_LOOKBACK_YEARS)
        if _is_pipeline(p) or within_lookback:
            keep.append(p)
    return keep


def delivery_tieout(props, series, as_of, lookback=4, subject_delivery=None):
    """Per-TTM-window delivered-units tie-out: roster (+ subject) vs CoStar's
    submarket deliveries series. Returns [{k, start, end, costar, roster,
    subject, gap, members}] for windows -Ylookback..Y0. `subject_delivery` is the
    subject's own ((y, q), units) — CoStar's submarket total includes it, the
    competitive roster excludes it, so it must be added back before comparing.
    The residual `gap` should be ~0 (sub-50-unit product aside)."""
    if not series:
        return []
    aq = quarter_index(*as_of)
    rows = []
    for k in range(lookback, -1, -1):
        end, start = aq - 4 * k, aq - 4 * k - 3
        costar = sum((v.get("deliveries") or 0) for (y, q), v in series.items()
                     if start <= quarter_index(y, q) <= end)
        members = [p for p in props if p.deliv_year and p.deliv_q
                   and start <= quarter_index(p.deliv_year, p.deliv_q) <= end]
        roster = sum(p.units or 0 for p in members)
        # only CoStar-tracked comps can tie to CoStar's own series; RealPage-only
        # deliveries are real supply CoStar misses — reported separately
        roster_cs = sum(p.units or 0 for p in members if "CoStar" in p.sources)
        rp_only = roster - roster_cs
        subj = 0
        if subject_delivery:
            (sy, sq), su = subject_delivery
            if start <= quarter_index(sy, sq) <= end:
                subj = su or 0
        rows.append({"k": k, "start": start, "end": end, "costar": costar,
                     "roster": roster, "roster_cs": roster_cs, "rp_only": rp_only,
                     "subject": subj, "gap": costar - roster_cs - subj,
                     "members": members})
    return rows


def reconcile_deliveries(props, series, as_of, lookback=4, subject_delivery=None,
                         authoritative=False):
    """Print delivered-units reconciliation vs CoStar's analytics series per TTM.

    For each historical trailing-12-month window, compares the named roster comps'
    delivered units (+ the subject's, added back) to CoStar's submarket
    `deliveries`. They should tie; a small positive residual is sub-50-unit
    product CoStar counts but the 50-unit property pull can't itemize. A residual
    beyond that means a 50+ comp is missing or mis-dated — the case worth
    catching (see SKILL.md §3a)."""
    rows = delivery_tieout(props, series, as_of, lookback, subject_delivery)
    if not rows or not any(r["costar"] or r["roster"] for r in rows):
        return
    ql = lambda i: f"Q{i % 4 + 1} {i // 4}"
    print("\n  Delivered-units reconciliation vs CoStar analytics (TTM windows):")
    flagged = False
    for r in rows:
        lab = f"-Y{r['k']}" if r["k"] else "Y0"
        subj_txt = f" + subject {r['subject']:,}" if r["subject"] else ""
        rp_txt = (f"  (+{r['rp_only']:,} RealPage-only supply CoStar misses)"
                  if r["rp_only"] else "")
        diff = r["gap"]
        flag = ""
        if diff > 0:
            flag = f"  (+{diff:,.0f} residual = sub-50 product?)"
        elif diff < 0:
            flag = f"  (roster exceeds CoStar by {-diff:,.0f} — check pins)"; flagged = True
        print(f"    {lab:>3} [{ql(r['start'])}..{ql(r['end'])}]  "
              f"CoStar {r['costar']:>6,.0f}  |  roster (CoStar-tracked) "
              f"{r['roster_cs']:>6,}{subj_txt}{flag}{rp_txt}")
        if diff >= 50:
            flagged = True
    if flagged:
        print("    ⚠ Reconcile the flagged window(s): account for sub-50 product, "
              "else look for a missing/mis-dated 50+ comp (SKILL.md §3a)."
              + ("" if authoritative else
                 " Supplying the CoStar PER-PROPERTY analytics export "
                 "(--costar-property-analytics) makes the pins authoritative — "
                 "these windows then tie."))


RADIUS_MI = 5.0            # the analysis radius; CoStar's export is exactly this


def drop_beyond_radius(props, max_mi=RADIUS_MI, eps=0.05):
    """Remove comps whose straight-line distance from the subject exceeds the
    radius. CoStar-listed comps use CoStar's exact lat/lon (always in-radius), so
    this only removes RealPage-only pipeline deals that geocode outside the ring —
    which belong to an adjacent submarket and shouldn't be in a 5-mile analysis.
    Mutates props in place and returns the dropped list (for logging)."""
    keep, dropped = [], []
    for p in props:
        if p.proximity_mi is not None and p.proximity_mi > max_mi + eps:
            dropped.append(p)
        else:
            keep.append(p)
    props[:] = keep
    return dropped


def subject_latlng_from_roster(costar_roster_path, subject_name):
    """Return 'lat,lng' for the subject from the CoStar roster's Latitude/Longitude
    columns (newer exports carry them), else None. This anchors the subject exactly
    without geocoding — the export's own coordinate for the subject building."""
    key = name_key(subject_name)
    for p in parse_costar_roster(costar_roster_path):
        if name_key(p.name) == key and p.lat is not None and p.lng is not None:
            return f"{p.lat},{p.lng}"
    return None


def load_latlng(path):
    """Analyst-supplied coordinates for comps CoStar doesn't geolocate.

    CSV with headers `property, latitude, longitude`. Returns {name_key: (lat,
    lng)}. Used to fill the RealPage-only pipeline deals so the map can be built
    from exact points instead of unreliable geocodes."""
    import csv
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            r = {(k or "").strip().lower(): v for k, v in r.items()}
            nm = (r.get("property") or "").strip()
            lat, lng = _float(r.get("latitude")), _float(r.get("longitude"))
            # Tolerate a combined "lat, lng" pasted into the latitude cell (common).
            if lat is None and r.get("latitude") and "," in str(r["latitude"]):
                parts = str(r["latitude"]).split(",")
                if len(parts) == 2:
                    lat, lng = _float(parts[0]), _float(parts[1])
            if nm and lat is not None and lng is not None:
                out[name_key(nm)] = (lat, lng)
    return out


def apply_latlng(props, mapping):
    for p in props:
        ll = mapping.get(name_key(p.name))
        if ll:
            p.lat, p.lng = ll


def compute_proximity(props, subject_latlng):
    """Set p.proximity_mi = straight-line miles from the subject to each comp,
    using **exact lat/lon only** (CoStar's export or analyst-supplied) — never
    geocoding. Comps without a coordinate are left as None (unknown), which keeps
    them in the chart but flags them as needing coordinates before the map."""
    if not subject_latlng:
        return
    subj_ll = tuple(float(x) for x in subject_latlng.split(","))
    for p in props:
        if p.lat is not None and p.lng is not None:
            p.proximity_mi = geo.haversine_miles(subj_ll, (p.lat, p.lng))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subject-name", required=True)
    ap.add_argument("--subject-address", default="")
    ap.add_argument("--costar-roster", required=True)
    ap.add_argument("--costar-analytics", required=True)
    ap.add_argument("--realpage", required=True)
    ap.add_argument("--costar-property-analytics", default=None,
                    help="CoStar PER-PROPERTY analytics export (quarterly series "
                         "per building). Strongly recommended: pins each comp's "
                         "delivery quarter authoritatively (the TTM windows then "
                         "tie to the overall deliveries series exactly), fills "
                         "occupancy gaps, and doubles as the subject rent history "
                         "(--costar-subject-rents defaults to this file).")
    ap.add_argument("--out", required=True)
    ap.add_argument("--as-of", default=None,
                    help="Override analysis quarter (Y0 = TTM ending here), e.g. "
                         "'2025 Q3'. Default: the latest COMPLETE quarter in the "
                         "analytics file (a partial QTD quarter is never used).")
    ap.add_argument("--close", default=None,
                    help="Close quarter (Y1 start / hold-year 1 anchor), e.g. '2025 Q4'. "
                         "Default: as-of + 2 quarters. Editable in the workbook afterward.")
    ap.add_argument("--target", type=float, default=DEFAULT_STABILIZATION_TARGET)
    ap.add_argument("--occ-source", choices=("costar", "realpage"), default="costar",
                    help="Which source's occupancy to display (default: costar)")
    ap.add_argument("--rent-source", choices=("costar", "realpage", "average"),
                    default="costar",
                    help="Source for the roster's Avg Mkt Rent (asking/market): "
                         "costar = CoStar asking (default); realpage = RealPage "
                         "asking IF its export carries one (else CoStar); average = "
                         "blend the available asking values. RealPage *effective* "
                         "rent is never used for this column.")
    ap.add_argument("--pipeline-dates", default=None,
                    help="CSV (property,est_delivery[,units]) of analyst-supplied "
                         "delivery quarters for pipeline deals, so they flow into "
                         "the absorption forecast.")
    ap.add_argument("--intake", default=None,
                    help="RR-T12 underwriting intake .xlsx (subject HelloData rents "
                         "+ financial-statement occupancy for the subject rows). If you "
                         "don't have a pre-built intake, use --hellodata (+ --t12) "
                         "instead — the skill computes the same mix-weighted subject "
                         "rows itself and needs no rr-t12-processor.")
    ap.add_argument("--hellodata", default=None,
                    help="HelloData 'Unit Details' CSV — either the subject-only "
                         "pull or the 5-MILE multi-property export. Drives the "
                         "subject's mix-weighted market/effective rent rows (no "
                         "--intake needed), and when it covers the comps, their "
                         "mix-weighted roster rents + the lease-up occupancy/"
                         "leasing-pace read.")
    ap.add_argument("--t12", default=None,
                    help="Subject's T-12 operating statement .xlsx — supplies the "
                         "subject occupancy row (1 − vacancy/AGPR); pairs with "
                         "--hellodata.")
    ap.add_argument("--costar-subject-rents", default=None,
                    help="CoStar per-property (50-unit) analytics export, used for "
                         "subject rent history before HelloData coverage begins.")
    ap.add_argument("--realpage-subject-rents", default=None,
                    help="RealPage per-property 10-yr rent export (alternative "
                         "subject rent source; the better-tracking of CoStar/"
                         "RealPage vs HelloData is auto-selected).")
    ap.add_argument("--diligence", default=None,
                    help="Filled per-project research CSV (see the emitted "
                         "…__diligence_TEMPLATE.csv) — adds a Diligence + shadow-"
                         "supply sheet and folds researched delivery dates back in.")
    ap.add_argument("--latlng", default=None,
                    help="CSV (property,latitude,longitude) of analyst-supplied "
                         "coordinates for comps CoStar doesn't geolocate (RealPage-"
                         "only pipeline deals). Needed to build the map when the "
                         "CoStar export doesn't cover every comp — see the emitted "
                         "…__map_latlng_TEMPLATE.csv.")
    ap.add_argument("--no-model-link", action="store_true",
                    help="Don't wire the subject rows to the underwriting model. "
                         "By default the subject Market Rent / Effective Rent / "
                         "Occupancy rows (Y0..Y6) carry IFERROR'd internal refs to "
                         "'Cash Flow (Annual)' rows 4/5/14 (Y0<-F, Y1..Y6<-K:P), so "
                         "the tab is ready to drag into / embed in the model and "
                         "shows clean blanks until then. Pass this for a pure "
                         "standalone chart with no model references.")
    ap.add_argument("--model-sheet", default="Cash Flow (Annual)",
                    help="Model tab the subject-row refs point to "
                         "(default: 'Cash Flow (Annual)').")
    ap.add_argument("--no-map", action="store_true",
                    help="Skip the companion HTML map. By default the run writes a "
                         "<subject>__Map.html alongside the chart.")
    ap.add_argument("--subject-latlng", default=None,
                    help="Pin the subject anchor exactly as 'lat,lng' (overrides "
                         "geocoding for both the Proximity column and the map). Use when "
                         "the mailing address geocodes to a road centroid / wrong spot.")
    args = ap.parse_args(argv)

    an = parse_costar_analytics(args.costar_analytics)
    latest_inv, deliveries, latest_label = an.latest_inv, an.deliveries, an.latest_label
    series, latest_uc = an.series, an.latest_uc
    # Y0 anchors to the latest COMPLETE quarter by default — a 10-day-old "QTD"
    # row must not define a TTM window.
    as_of = parse_as_of(args.as_of or an.complete_label or latest_label)

    # CoStar per-property analytics: authoritative delivery pinning + per-building
    # occupancy history + subject rent history. --costar-subject-rents is the same
    # export format, so it doubles as the pinning source when the dedicated flag
    # isn't given.
    pp_path = args.costar_property_analytics or args.costar_subject_rents
    pp = parse_costar_property_analytics(pp_path) if pp_path else None
    # HelloData 5-mile export: rows per property (comp rents / lease-up read).
    import subject_intake
    hd_by_prop = (subject_intake.hellodata_rows_by_property(args.hellodata)
                  if args.hellodata else {})

    props = build_competitive_roster(
        args.costar_roster, args.realpage, deliveries, as_of,
        args.subject_name, args.subject_address, args.target,
        args.occ_source, args.rent_source, pp=pp, hd_by_prop=hd_by_prop)

    # The subject's own delivery ((y,q), units) — added back in the tie-outs and
    # the Y0 supply when it delivered inside a window.
    subject_delivery = None
    if pp:
        nm = make_name_matcher(pp.keys())(args.subject_name)
        if nm and pp[nm]["deliveries"]:
            subject_delivery = max(pp[nm]["deliveries"], key=lambda t: t[1])

    # Apply analyst-supplied pipeline delivery quarters so they enter the forecast.
    if args.pipeline_dates:
        applied = load_pipeline_dates(args.pipeline_dates)
        apply_pipeline_dates(props, applied)

    diligence_rows = None
    if args.diligence:
        diligence_rows = load_diligence(args.diligence)
        apply_diligence(props, diligence_rows)

    # Coordinates come from exact lat/lon only (no geocoding guesses): CoStar's
    # export, plus any analyst-supplied --latlng CSV for comps CoStar can't place.
    import os
    import csv as _csv
    if args.latlng:
        apply_latlng(props, load_latlng(args.latlng))
    # Subject anchor: --subject-latlng, else the subject's own CoStar roster coord.
    subj_ll = args.subject_latlng or subject_latlng_from_roster(
        args.costar_roster, args.subject_name)
    compute_proximity(props, subj_ll)
    # Enforce the 5-mile radius: any comp with a KNOWN coordinate beyond it is
    # dropped (comps without a coordinate stay — their distance is unverified).
    beyond = drop_beyond_radius(props)
    if beyond:
        print("  Excluded (beyond 5-mi radius; RealPage-only / adjacent submarket):")
        for p in sorted(beyond, key=lambda x: -(x.proximity_mi or 0)):
            print(f"      {p.name[:34]:34s} {p.proximity_mi:.1f} mi  "
                  f"[{'+'.join(sorted(p.sources))}]")

    # Subject rent/occupancy rows: from a pre-built RR-T12 intake, OR computed here
    # from the raw HelloData CSV (+ T-12) — the latter needs no rr-t12-processor.
    # The HelloData CSV may be the 5-mile multi-property export; the subject's own
    # rows are filtered out of it by name.
    if args.intake:
        subj_monthly = parse_intake_subject(args.intake)
    elif args.hellodata or args.t12:
        subj_monthly = subject_intake.subject_monthly_from_raw(
            args.hellodata, args.t12, subject_name=args.subject_name)
    else:
        subj_monthly = {}
    # Subject quarterly history: explicit --costar-subject-rents, else the
    # per-property analytics file (same format) supplies it.
    if args.costar_subject_rents:
        subj_costar = parse_costar_subject_rents(args.costar_subject_rents,
                                                 args.subject_name)
    elif args.costar_property_analytics:
        subj_costar = parse_costar_subject_rents(args.costar_property_analytics,
                                                 args.subject_name)
    else:
        subj_costar = {}
    subj_realpage = (parse_realpage_subject_rents(args.realpage_subject_rents, args.subject_name)
                     if args.realpage_subject_rents else {})

    close_q = parse_as_of(args.close) if args.close else None
    write_workbook(props, args.subject_name, latest_inv, latest_label,
                   as_of, args.target, args.out, series=series, latest_uc=latest_uc,
                   subj_monthly=subj_monthly, subj_costar=subj_costar,
                   subj_realpage=subj_realpage, diligence_rows=diligence_rows,
                   model_link=not args.no_model_link, model_sheet=args.model_sheet,
                   close_quarter=close_q, qtd=an.qtd,
                   subject_delivery=subject_delivery)

    # Emit templates: undated pipeline + a per-project research template.
    base = os.path.splitext(args.out)[0]
    n_undated = emit_pipeline_template(props, base + "__pipeline_dates_TEMPLATE.csv")
    emit_diligence_template(props, base + "__diligence_TEMPLATE.csv")

    # Console reconciliation report
    print(f"\nSupply chart written: {args.out}")
    print(f"As-of quarter: {fmt_quarter(*as_of)}  |  "
          f"Total current inventory (CoStar): {latest_inv:,}")
    print(f"Competitive new-construction properties: {len(props)}\n")
    for bucket, _ in BUCKET_ORDER:
        members = [p for p in props if p.bucket == bucket]
        if not members:
            continue
        u = sum(p.units or 0 for p in members)
        print(f"  {bucket} — {len(members)} props, {u:,} units")
        for p in sorted(members, key=lambda x: -p_qi(x)):
            occ = f"{p.occupancy:.1%}" if p.occupancy is not None else "  —  "
            print(f"      {p.name[:34]:34s} {str(p.units or '—'):>5} u  "
                  f"{p.est_delivery or 'TBD':>8}  occ {occ:>6}  "
                  f"[{'+'.join(sorted(p.sources))}]"
                  f"{('  | ' + '; '.join(p.notes)) if p.notes else ''}")
    reconcile_deliveries(props, series, as_of, subject_delivery=subject_delivery,
                         authoritative=bool(pp))
    if n_undated:
        print(f"\n  {n_undated} pipeline deal(s) have no delivery quarter and are "
              f"NOT in the absorption forecast yet.\n"
              f"  Fill {base}__pipeline_dates_TEMPLATE.csv (--pipeline-dates), or "
              f"research them via {base}__diligence_TEMPLATE.csv (--diligence).")
    print()

    # ---- Companion HTML map — ONLY when every comp has an exact coordinate ----
    # No geocoding guesses: if any competitive comp lacks a lat/lon (RealPage-only
    # pipeline deals CoStar doesn't place), the chart is still written but the map
    # is held back. We emit a template of the missing comps to fill and re-run.
    if not args.no_map:
        map_out = (base[:-len("__Supply_Chart")] if base.endswith("__Supply_Chart")
                   else base) + "__Map.html"
        missing = [p for p in props if p.lat is None or p.lng is None]
        if not subj_ll:
            print("  ⚠ HTML map NOT generated: the subject has no coordinate. "
                  "Pass --subject-latlng \"lat,lng\" (or add Latitude/Longitude to "
                  "the CoStar roster) and re-run.")
        elif missing:
            tmpl = base + "__map_latlng_TEMPLATE.csv"
            with open(tmpl, "w", newline="", encoding="utf-8") as fh:
                w = _csv.writer(fh)
                w.writerow(["property", "bucket", "units", "address",
                            "latitude", "longitude"])
                for p in sorted(missing, key=lambda x: x.name):
                    w.writerow([p.name, p.bucket, p.units or "",
                                " ".join(x for x in [p.address, p.city, p.state,
                                                     p.zipcode] if x), "", ""])
            print(f"\n  ⚠ HTML map NOT generated yet — {len(missing)} competitive "
                  f"comp(s) have no exact lat/lon (not in the CoStar export):")
            for p in sorted(missing, key=lambda x: x.name):
                print(f"      {p.name[:36]:36s} [{'+'.join(sorted(p.sources))}]  "
                      f"{(p.address or '').strip()} {p.city or ''} {p.zipcode or ''}")
            print(f"  The supply chart is written. To get the map, fill the "
                  f"latitude/longitude for these in:\n      {tmpl}\n"
                  f"  then re-run with  --latlng {os.path.basename(tmpl)}")
        else:
            try:
                import build_map
                shadow = [r for r in (diligence_rows or []) if r.get("type") == "shadow"]
                placed, _ = build_map.build_map(
                    props, args.subject_name, args.subject_address, subj_ll,
                    map_out, shadow or None,
                    build_map._subject_meta(args.costar_roster, args.subject_name))
                print(f"Companion HTML map written: {map_out}  ({placed} properties)")
            except Exception as e:
                print(f"  (map skipped: {type(e).__name__}: {e}\n"
                      f"   the map needs network access for basemap tiles; "
                      f"pass --no-map to skip it.)")


if __name__ == "__main__":
    sys.exit(main())
