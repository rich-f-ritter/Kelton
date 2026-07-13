# The Kelton — Real Estate Tax Analysis

**Property:** The Kelton Apartments (Phase 1 Plat), 301 S 1100 W, American Fork, UT 84003 — 240 units
**Owner of record:** MWIC Kelton Commercial LLC (Mountain West Investment Corp., 201 Ferry St SE Ste 400, Salem, OR 97301)
**Tax jurisdiction:** Utah County — Tax Area **060, American Fork City**
**Parcels:** 15 serials, **44:238:0001 → 44:238:0015** (Kelton Apartments Phase 1 Plat, Lots 1–15)
**Sources:** 2025 paid tax bills + 2026 assessed-value dashboards, all 30 county PDFs (`/home/user/Kelton/data/tax/…`). Total rentable SF (233,406) from the 6/16/2026 rent roll.
**Prepared:** 2026-07-13

---

## 1. Current in-place taxes (what the buyer inherits)

| Metric | Value |
|---|---|
| **Total 2025 net taxes (15 parcels, all paid, $0 balance)** | **$302,466.54** |
| Tax per unit (÷ 240) | **$1,260.28** |
| Tax per SF (÷ 233,406 SF) | **$1.30** |
| Total assessed **market** value 2025 (tax base year) | $62,139,200 |
| Total assessed **market** value 2026 (latest) | $62,607,400 |
| Total land area | 10.29 acres |
| Effective tax rate (2025 tax ÷ 2025 market value) | **0.4868%** |

2025 bills were paid in full — 14 parcels by CoreLogic Commercial on 11/26/2025, and the commercial parcel 001 by InstantPayments on 11/06/2025. No penalties or open balances on any parcel. Parcel 008 shows a $177.89 attached-personal-property adjustment that was posted and then reversed (net $0).

> **The RedIQ operating statement understates taxes.** RedIQ books **$293,799.55**, which is exactly the 14 apartment parcels (serials 002–015). It **omits parcel 001** ($8,666.99, the 257 S 1100 W commercial/retail pad). The true all-in county tax the buyer inherits is **$302,466.54** — use this, not the RedIQ line. (Reconciliation in §6.)

---

## 2. Per-parcel detail (auditable)

Full data with the land/improvement split is in `Kelton_Tax_Parcel_Detail.csv`. Summary:

| Serial | Address / Lot | Acres | 2025 Net Tax | MV 2022 | MV 2023 | MV 2024 | MV 2025 | MV 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0001 | 257 S 1100 W (Lot 1, commercial) | 0.325 | $8,666.99 | 1,343,900 | 636,100 | 753,600 | 992,100 | 1,026,400 |
| 0002 | 1027 W 250 S Unit A (Lot 2) | 0.763 | $27,792.40 | 627,100 | 1,686,300 | 3,182,300 | 5,784,300 | 5,810,800 |
| 0003 | 1027 W 250 S Unit B (Lot 3) | 1.034 | $14,674.34 | 120,000 | 1,076,400 | 2,317,800 | 3,054,100 | 3,084,200 |
| 0004 | 1027 W 250 S Unit D (Lot 4) | 0.620 | $15,285.51 | 120,000 | 1,709,500 | 2,104,400 | 3,181,300 | 3,199,100 |
| 0005 | 1027 W 250 S Unit C (Lot 5) | 0.578 | $27,792.40 | 240,000 | 2,306,300 | 3,088,600 | 5,784,300 | 5,810,700 |
| 0006 | 301 S 1100 W Unit M (Lot 6) | 0.700 | $27,792.40 | 341,400 | 2,926,300 | 3,151,000 | 5,784,300 | 5,810,800 |
| 0007 | 301 S 1100 W Unit N (Lot 7) | 0.688 | $9,231.94 | 120,000 | 1,606,700 | 1,884,100 | 1,921,400 | 2,062,200 |
| 0008 | 301 S 1100 W Unit L (Lot 8) | 1.384 | $27,792.40 | 240,000 | 3,420,600 | 3,655,900 | 5,784,300 | 5,810,800 |
| 0009 | 301 S 1100 W Unit K (Lot 9) | 0.765 | $14,815.60 | 120,000 | 2,081,100 | 2,243,300 | 3,083,500 | 3,077,400 |
| 0010 | 301 S 1100 W Unit J (Lot 10) | 0.437 | $27,792.40 | 240,000 | 2,926,300 | 3,015,700 | 5,784,300 | 5,810,800 |
| 0011 | 301 S 1100 W Unit I (Lot 11) | 0.884 | $27,792.40 | 240,000 | 3,207,500 | 3,329,700 | 5,784,300 | 5,810,800 |
| 0012 | 301 S 1100 W Unit H (Lot 12) | 0.483 | $15,285.51 | 120,000 | 1,867,800 | 2,031,500 | 3,181,300 | 3,199,200 |
| 0013 | 301 S 1100 W Unit G (Lot 13) | 0.585 | $15,285.51 | 120,000 | 1,867,800 | 2,083,600 | 3,181,300 | 3,199,200 |
| 0014 | 301 S 1100 W Unit F (Lot 14) | 0.398 | $14,674.34 | 120,000 | 1,867,800 | 1,989,900 | 3,054,100 | 3,084,200 |
| 0015 | 301 S 1100 W Unit E (Lot 15) | 0.649 | $27,792.40 | 240,000 | 2,926,300 | 3,125,000 | 5,784,300 | 5,810,800 |
| **TOTAL** | **15 parcels** | **10.29** | **$302,466.54** | **4,352,400** | **32,112,800** | **37,956,400** | **62,139,200** | **62,607,400** |

*Data note:* The county files for parcel 002 are swapped between the two folders — `2025_Tax_Bill/442380002.pdf` actually holds the assessed-value dashboard and `2026_Assessed_Value/442380002.pdf` holds the tax bill. Both were captured; parcel 002 = $27,792.40 tax / $5,784,300 MV 2025.

---

## 3. Assessment trend 2022 → 2026

| Year | Total Market Value | YoY change | Per unit | Notes |
|---|---:|---:|---:|---|
| 2022 | $4,352,400 | — | $18,135 | Raw land / start of construction (serial life begins 2022; most lots at $120k–$240k) |
| 2023 | $32,112,800 | +$27,760,400 (+637.8%) | $133,803 | Improvements coming online |
| 2024 | $37,956,400 | +$5,843,600 (+18.2%) | $158,152 | Continued build-out |
| 2025 | $62,139,200 | +$24,182,800 (+63.7%) | $258,913 | Fully improved / lease-up |
| 2026 | $62,607,400 | +$468,200 (+0.8%) | $260,864 | **Stabilized — essentially flat** |

The steep 2022→2025 ramp is **construction completion being assessed, not market appreciation** — this is a newly built asset. The key underwriting signal is that the assessment has now **stabilized at ~$62.6M (~$260,900/unit)**. That is the assessor's current market-value opinion, and it sits at the **low end of, and below, likely trade value.**

---

## 4. Effective rate, exemption mechanics & certified rate

Reverse-engineering the bills against the assessments yields a fully consistent model:

- **Certified tax rate, Tax Area 060 (2025): 0.87360% (0.0087360) of *taxable* value.**
- **14 apartment parcels (002–015):** taxed on **55% of market value** — i.e., they receive Utah's **45% primary residential exemption** (Utah Code §59‑2‑103). Tenant-occupied apartments qualify. Effective rate on market value = 0.55 × 0.87360% = **0.4805%**.
  - Check, parcel 002: $5,784,300 × 0.55 × 0.0087360 = **$27,792.40** ✓ (matches to the penny; same for every residential parcel).
- **Commercial parcel (001):** taxed on **100% of market value** (no residential exemption). Effective rate = **0.87360%**.
  - Check: $992,100 × 0.0087360 = **$8,666.99** ✓.
- **Blended portfolio effective rate on total market value = 0.4868%** (slightly above the 0.4805% residential rate because parcel 001, ~1.6% of value, pays the full rate).

**Assumption stated:** the multifamily units carry the residential exemption (55% taxable), confirmed by the math above. If a future assessor ever challenged owner-occupancy status on any unit, that parcel's effective rate would jump toward the 0.8736% full rate — a downside not currently in the bills.

---

## 5. Reassessment-on-sale risk (KEY underwriting item)

Utah reassesses to **fair market value every year** (no Prop‑13 acquisition-value cap), and an arm's-length **sale is the strongest evidence of value**. Because the property currently sits on the roll at only **~$260,900/unit ($62.6M)**, a trade above that will pull the assessment up toward the purchase price and reset taxes. RealPage 5‑mile comps for similar assets run **~$220k–$375k/unit**, so a 240‑unit trade plausibly clears the current assessed value by 15%+.

Scenarios apply the **blended effective rate of 0.4868%** to the reassessed value (= purchase price), holding the certified rate constant:

| Purchase basis | Total value | Reassessed tax | Δ vs in-place $302,467 | Tax/unit | Tax/SF |
|---|---:|---:|---:|---:|---:|
| $250,000/unit | $60,000,000 | $292,054 | **−$10,413 (−3.4%)** | $1,217 | $1.25 |
| $275,000/unit | $66,000,000 | $321,259 | **+$18,793 (+6.2%)** | $1,339 | $1.38 |
| **$300,000/unit** | **$72,000,000** | **$350,465** | **+$47,998 (+15.9%)** | **$1,460** | **$1.50** |
| $325,000/unit | $78,000,000 | $379,670 | **+$77,203 (+25.5%)** | $1,582 | $1.63 |
| $350,000/unit | $84,000,000 | $408,875 | **+$106,409 (+35.2%)** | $1,704 | $1.75 |

Read-through:
- At **≤ ~$260k/unit** the current assessment already captures the value — **little/no reset** (the $250k row is mechanically below in-place because the current roll is fuller than that price).
- At a **~$300k/unit** trade (comp midpoint), expect taxes to reset from **$302k to ~$350k (+16%, +$48k/yr, +$200/unit)**.
- Every **+$25k/unit** of price adds roughly **+$29k/yr** of tax (≈ +$122/unit).

**Truth-in-Taxation nuance:** under TnT the certified rate ratchets *down* when values rise so each taxing entity's total revenue stays flat (ex-new-growth). But that protects the *aggregate levy*, not a single reassessed property — when one asset is written up while others hold, its share of the pie (and its bill) still rises largely as modeled. Treat any rate step-down as a modest partial offset, not a reason to skip the reset. The exact reset is at the assessor's discretion and timing (typically the lien date following the sale).

---

## 6. Reconciliation to the RedIQ booked figure

| Item | Amount |
|---|---:|
| County-paid 2025 taxes, all 15 parcels | $302,466.54 |
| Less: parcel 001 (257 S 1100 W, commercial pad) | −$8,666.99 |
| **= RedIQ "Real Estate Taxes" (Oct-2025 accrual)** | **$293,799.55** |

The gap is **exactly parcel 001** — to the penny. RedIQ's single Oct‑2025 lump ($293,799.55) is the annual accrual for the **14 residential apartment parcels only**; the standalone commercial parcel was booked elsewhere or excluded from the residential operating statement. **The buyer acquires all 15 parcels**, so the in-place tax for underwriting is **$302,466.54**, i.e. the RedIQ line **plus $8,667**.

---

## 7. Recommended year‑1 underwriting tax number

1. **Do not underwrite the RedIQ $293,800** — it omits the commercial parcel. The correct in-place figure is **$302,467** ($1,260/unit).
2. **Underwrite the reassessment.** Because Utah resets to market on sale and the property is currently on the roll below likely trade value, Year‑1 taxes should be tied to the **purchase price**, not the trailing bill.

**Recommended Year‑1 real estate tax = ~$350,000 (≈ $1,460/unit, ~$1.50/SF)**, based on a ~$300k/unit / ~$72M basis (comp midpoint) reassessed at the 0.4868% effective rate. Scale with the actual price using the table in §5:
- Conservative floor (no reset / low basis): **$302,467** in-place.
- Base case (~$300k/unit): **~$350,000**.
- Higher basis (~$350k/unit): **~$409,000**.

**Flags:** (a) reset timing and exact allocation are at the assessor's discretion; (b) the 45% residential exemption is doing heavy lifting — protect owner-occupancy documentation, as loss of the exemption on any parcel roughly doubles that parcel's rate; (c) a small Truth-in-Taxation rate step-down may modestly soften the reset; (d) confirm whether the commercial parcel 001 is being conveyed and how its (higher) full-rate tax is handled in the model.

---

*All figures traceable to county serials 44:238:0001–0015. Per-parcel raw extract: `Kelton_Tax_Parcel_Detail.csv`.*
