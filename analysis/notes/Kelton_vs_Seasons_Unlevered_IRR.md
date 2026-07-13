# Kelton vs. Seasons of Traverse Mountain — Unlevered IRR bridge + tax finding

Both are TMG models, same template, same market (Utah County — American Fork vs. Lehi/Traverse Mtn).

## Headline
| Metric | **Kelton** | **Seasons** | Note |
|---|---|---|---|
| Units | 240 | 440 | Kelton smaller |
| Vintage | 2022 (newer) | older / value-add | |
| Purchase price | $55.0M | $130.25M | |
| **Price / unit** | **$229,167** | **$296,023** | Kelton ~$67k/u cheaper |
| Y1 cap rate | **4.92%** | 4.62% | Kelton higher entry yield |
| T3 TMG adj cap | 4.86% | 4.66% | |
| Exit cap | 4.75% | 4.75% | same |
| Capex / unit | $7,250 | $20,826 | Seasons heavy value-add |
| Y1–Y6 NOI CAGR | 3.19% | **5.30%** | Seasons much higher growth |
| T12–Y6 NOI CAGR | 1.21% | 3.80% | |
| Appreciation CAGR | 4.18% | 4.56% | |
| Exit price / unit | $281,179 | $369,967 | |
| **Unlevered IRR** | **8.24%** | **7.73%** | **Kelton +51 bps** |
| Levered IRR | 11.05% | 12.91% | Seasons wins levered |

## What drives Kelton's higher UNLEVERED IRR (+51 bps) despite far lower NOI growth
Unlevered IRR ≈ entry yield + income growth ± cap-rate shift − capex timing.

1. **Entry yield (biggest driver, +Kelton).** Kelton buys at a 4.92% Y1 cap vs Seasons 4.62% — ~30 bps more cash yield from day one. On an unlevered basis the going-in yield dominates.
2. **Cap-rate shift (+Kelton).** Kelton enters ~4.86% and exits 4.75% → ~11 bps **compression** (value tailwind). Seasons enters ~4.66% and exits 4.75% → ~9 bps **expansion** (value headwind). Kelton sells tighter than it bought; Seasons sells wider.
3. **Capex timing (+Kelton unlevered).** Seasons spends $20,826/u ($9.2M) of mid-hold capex — cash out that drags unlevered IRR. Kelton spends $7,250/u ($1.7M).
4. **NOI growth (−Kelton / +Seasons, the offset).** Seasons' value-add drives 5.30% Y1–Y6 NOI CAGR vs Kelton 3.19% (T12–Y6: 3.80% vs 1.21%). This nearly closes the gap — which is why the unlevered IRRs are within ~50 bps and why **Seasons flips ahead on the levered IRR** (leverage amplifies its growth): 12.91% vs 11.05%.
5. **Appreciation** slightly favors Seasons (4.56% vs 4.18%).

**Read:** Kelton = a newer, stabilized asset bought at a higher going-in yield and a low basis, with modest growth — front-loaded, yield-driven unlevered return. Seasons = an older value-add bought tighter, with heavy capex and strong NOI growth — back-loaded, growth-driven return that only pulls ahead once you add leverage.

## Is there something wrong with Kelton's taxes? — Yes, worth pressure-testing
The Kelton model **reassesses the taxable value DOWN to the $55M purchase price on sale**, which *cuts* taxes below the in-place level:

- `Taxes!` Reassessment for Sale = **Yes**, Reassmnt Year 2027, **Reassmnt % = 100%** → 2027 Assessed Value set to **$55,000,000**.
- Current county assessment (2026) = **$62,607,400** ($260,864/u); in-place tax **$302,467**.
- Because purchase ($55M) < current assessment ($62.6M), the reset **lowers** the bill: **2027 tax = $265,714** (−$36.8k vs in-place), then grows 3%/yr; it doesn't exceed the current $302k until ~2032.

**Why that's a flag:**
1. **It assumes an automatic assessment reduction to the sale price.** Utah assesses at market value, and a recent arm's-length sale is good appeal evidence — but the county does **not** auto-lower to a below-assessment sale price; it takes a successful appeal, which counties often resist. Underwriting an automatic ~$37k/yr tax cut is optimistic.
2. **It rides on a low basis.** $55M = $229k/u is below both Kelton's **own county assessment** ($261k/u) and the **Seasons comp** ($296k/u) — for a *newer* asset. If the true basis is higher (or the appeal fails), taxes stay ~$302k **and rise**, not fall.
3. **It's inconsistent with Seasons (same shop, same county).** Seasons does the opposite: Reassmnt % = **90.86%**, resetting its assessed value **UP** to $118.3M (91% of its $130.25M price, above its $105.7M current assessment) → 2027 tax **rises** to $527,857. Seasons underwrites taxes conservatively (up on sale); Kelton underwrites them favorably (down on sale).

**Impact:** the down-reset gives Kelton ~$30–40k/yr of tax relief early (~$780k of value at the 4.75% exit cap) that supports its NOI, its 4.92% entry cap, and thus part of the unlevered-IRR edge. Effective tax rate itself (~0.48%) is fine and matches the parcel-level analysis; the issue is the **basis and the direction of the reassessment**, not the rate.

**Recommendation:** test the deal with taxes reassessed *up* toward the actual purchase price (Seasons-style), or at minimum held flat at the in-place $302k, and see how much of the 51-bp unlevered edge survives. Also confirm whether $55M is the real basis or a placeholder — at $229k/u for a 2022 asset it looks low vs. the comp set.

---

## Follow-up 1: what's wrong with the tax on the Kelton residual

The reversion is `Sales Proceeds` (Cash Flow Annual O76) = **$67,482,947** = Year-6 forward NOI ($3,205,440) ÷ 4.75% exit cap. The tax embedded in that terminal NOI is broken in two ways:

1. **The tax module's value path is disconnected from the model's own value path.** On the `Taxes` tab the assessed value is reset DOWN to the $55M purchase price at going-in, then grown a flat **3%/yr** — so at the Year-5 exit (2031) it reads **$61.9M** (row 22) while the model is *simultaneously selling the asset for $67.5M*. Taxes are levied on ~$62–64M when the property changes hands at $67.5M.
2. **No exit reassessment for the incoming buyer.** The "Reassessment for Sale" logic fires only at going-in (down to $55M); it never steps the basis UP to the exit price for the next buyer. A buyer at $67.5M would be reassessed to ~$67.5M and pay ~$324k/yr (0.48%), vs the ~$306k baked into the terminal NOI.

**Effect:** the terminal NOI is over-earning on understated taxes (~$18k/yr too low at exit), which at the 4.75% cap inflates the reversion by **~$380k** — on top of the whole-hold benefit of the aggressive reassess-DOWN (taxes $30–40k/yr below in-place through ~2031). The residual should either grow the assessed value with the property's modeled value, or reassess to the exit price for the buyer. (Note: Seasons has the same value-path convention, but because it reassessed UP to 91% of price at going-in, its basis tracks reality far better — Kelton's is the aggressive one.)

## Follow-up 2: why Seasons pencils at ~$296k/unit and Kelton at ~$229k/unit

It is **not** rents and **not** unit size — those actually favor Kelton:
- **Achieved rent/unit is basically the same:** Kelton $1,464/occ unit (HD market $1,595) vs Seasons $1,473/occ unit (HD $1,473).
- **Unit size favors Kelton:** ~973 SF vs Seasons ~907 SF. On $/SF the gap is even starker — Kelton $235/SF vs Seasons $326/SF.

The $/door gap ($66.9k) comes from two things:

| Driver | Kelton | Seasons | Effect on gap |
|---|---|---|---|
| **NOI / unit (T12)** | $12,536 | $14,407 (+15%) | ~$38k (57%) |
| **Price ÷ NOI (multiple)** | 18.3× (5.47% cap) | 20.6× (4.87% cap) | ~$28k (43%) |

1. **NOI/unit (57% of the gap) = expense load, not revenue.** EGI/unit is nearly identical ($20,210 vs $20,449), but Kelton runs a **38% expense ratio vs Seasons' 29.5%**. Part is presentation — Kelton's RUBS is grossed up into both revenue and expense (RR-T12 convention), inflating the ratio without touching NOI; netting RUBS pulls Kelton to ~33%. The rest is genuinely heavier controllables, led by **utilities $2,051/unit vs $1,216/unit** — surprising for a newer building and worth diligence (metering/recovery structure).
2. **Multiple (43% of the gap) = value-add premium.** Seasons is bid at a richer 20.6× (tighter cap) because it carries a **~22% loss-to-lease** (in-place $1,473 vs the model's $1,902 market) vs Kelton's **~11%** ($1,483 vs $1,664) — far more embedded mark-to-market for a buyer to pay up for. **Caveat:** Seasons' $1,902 GPR market rent is ~29% above HelloData's $1,473 read, so that upside (and the price it justifies) looks aggressive and should be verified.

**Bottom line:** Kelton isn't the lower-quality asset — newer, bigger units, comparable rents. It's simply **bid at a cheaper basis (higher going-in cap) with less assumed upside**, while Seasons is bid up on a large (possibly aggressive) value-add roll. That cheaper Kelton basis is exactly why its *unlevered* IRR is higher despite weaker growth — and part of that basis advantage is the aggressive tax reassess-DOWN, which flatters both interim NOI and the residual.
