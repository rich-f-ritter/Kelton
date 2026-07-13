# The Kelton — Cross-Workstream Review (Underwriting Synthesis)

**Property:** The Kelton Apartments · 301 S 1100 W, American Fork, UT 84003 · 240 units (84×1BR / 132×2BR / 24×3BR) · built 2022 · Class B/B+ garden · owner Neighborly Ventures (title entity MWIC Kelton Commercial LLC).
**Prepared:** 2026-07-13 · Cross-Workstream Reviewer (synthesis layer over RR-T12 intake, Rent Comps, Supply Chart, Tax).
**Reviewer's role:** verify the four workstreams tie together and hand an underwriter one coherent picture. This is a review, not a re-run — the deliverables were not modified. Every number below was pulled from the committed workbooks/CSVs and re-checked (see `Reconciliation_Checks.csv`).

---

## 0. The numbers to underwrite (one box)

| Line | Figure | Source of truth |
|---|---:|---|
| Units / mix | 240 (84 / 132 / 24 by BR) | consistent across all four workstreams ✓ |
| **In-place EGR (T12 Jun'25–May'26)** | **$4,850,394** | RR-T12 intake (RedIQ-standardized) |
| **In-place OpEx** | **$1,841,644** | RR-T12 intake — *carries taxes at only $293,800; see §2/tax* |
| **In-place NOI (standardized)** | **$3,008,750** | RR-T12 intake — **use this, NOT operator's $3,361,990** |
| Occupancy (physical, in-place) | **93.75%** | rent roll 6/16/26 (225/15/0 of 240) — use for UW |
| Subject current market rent (HD T90 asking) | **$1,595 /u** | RR-T12 = Rent Comps (exact) |
| Subject in-place contract rent | **$1,483 /u** | RR-T12 unit mix |
| **True in-place taxes (all 15 parcels)** | **$302,467** ($1,260/u) | Tax analysis — intake understates by $8,667 |
| **Recommended Year-1 (reassessed) taxes** | **~$350,000** ($1,460/u) | Tax analysis, ~$300k/u basis |
| Forward 5-mi supply pipeline | **ZERO** (CoStar UC=0) | Supply chart |

---

## 1. How it all flows together (the value-creation through-line)

**The Kelton is a stabilized 2022 lease-up that is under-rented in a submarket with no forward supply, bought into a Utah tax reset.** The four workstreams stack into one thesis:

**(a) Start from the honest in-place NOI — $3.01M, not $3.36M.** The RR-T12 intake's most consequential finding: Neighborly's own statement prints "NET OPERATING INCOME" of **$3,361,990**, but that is overstated by **$353,240 (~12%)** because the operator books **property taxes ($293,800) + insurance ($59,440) BELOW its NOI line**. RedIQ (and the intake) correctly pull them into OpEx. Verified to the penny: operator NOI $3,361,990 − $353,240 = standardized NOI **$3,008,750**. Margin 62.0%, occupancy 93.75%. This is the base the rest of the thesis builds on. (One more haircut: the intake's OpEx carries taxes at only the RedIQ line of $293,800, which the tax workstream shows is $8,667 light — see §2.)

**(b) The rent upside is real and layered.** In-place **contract rent averages $1,483/u** while the subject's own **current market/asking rent (HelloData T90 executed) is $1,595/u** — a **loss-to-lease of ~$112/u (~7.5%)** that burns off as leases roll to current asking. Then the **Rent Comps** workstream tests whether $1,595 is itself full market: against a curated 10-comp garden Class-B set it is **~4% under** the unit-weighted comp market of **$1,660**. On $/SF the Kelton is essentially **at par** ($1.64 vs $1.66) — so the gap is a rent-level gap, not a size effect — and it is **concentrated in the 2BR (−5.2%, and 2BR is 55% of the units) and 3BR (−4.7%); the 1BR is already at market (−1.4%)**. Closing the 2BR gap alone drives most of the achievable lift. So there are two stacked rent levers: burn off ~$112/u of loss-to-lease, then push asking ~4% toward comps (2BR-led).

**(c) The market supports pushing rents — nearly immediately.** The **Supply Chart** answers *when*. The 5-mi ring holds **7,632 units**; trailing deliveries peaked at 1,310 units (-Y2) and have fallen to **528 in Y0** (essentially just Sanctuary's 519-unit lease-up). Critically, the **forward pipeline is ZERO** — CoStar under-construction = 0 as of Q2 2026, roster carries 0 UC / 0 proposed. With base demand of **725 u/yr** (trailing-3-yr CoStar avg) and no new supply, the ~534-unit gap to a 95% target is basically just Sanctuary absorbing, and **occupancy re-stabilizes to 95% by Y1 under Base (Y2 Bear, immediately Bull)**. A no-supply, re-stabilizing submarket is exactly the backdrop that lets an owner push rents rather than defend occupancy — and the subject's Y0 market rent ($1,588 mix-weighted TTM) sits **below the 16-property comp median of $1,724**, i.e. relative-value room against the newest product.

**(d) Net it against the tax reset.** Taxes are the single largest controllable OpEx line and the one that resets on sale. Utah reassesses to fair market value annually with no acquisition-value cap; the property currently sits on the roll at only **~$260,900/unit ($62.6M)**, below likely trade value. A **~$300k/unit (~$72M) trade resets taxes from ~$302k in-place to ~$350k (+$48k/yr, +16%)**. Because the intake only carries $293,800 of tax today, moving to the recommended **$350,000 Year-1 figure trims ~$56,200 off the intake NOI → a reassessed Year-1 NOI of ~$2,952,550 before any rent upside**. That is the correct starting NOI to grow the mark-to-market story from.

**Through-line in one sentence:** honest in-place NOI ≈ **$3.01M** (−~$56k for the tax reset → **~$2.95M** Year-1) → **~$112/u loss-to-lease + ~4% (2BR-led) mark-to-market to comps** → **supported by a zero-pipeline, re-stabilizing 5-mi market** that firms to 95% occupancy by Y1 → underwrite the rent ramp with confidence, but haircut NOI for the Utah reassessment and the RUBS/other-income and tax corrections below.

---

## 2. Cross-check consistency (verify, don't assume)

The workstreams share inputs (HelloData, the rent roll, CoStar/RealPage), so overlaps should agree. **They largely do.** Full side-by-side is in `Reconciliation_Checks.csv`; verdicts here.

### 2.1 Subject market rent — TIES ✓ (benign window difference)
| Source | Figure | Method |
|---|---:|---|
| RR-T12 intake — HD T90 asking (mix-wtd) | **$1,595** | trailing-90-day executed asking, mix-weighted |
| Rent Comps — subject Total-Gross | **$1,595** | same HD T90 executed asking (**exact match**) |
| Supply Chart — subject Y0 market | **$1,588** | HD mix-weighted over the **TTM window** (Q3'25–Q2'26) |

RR-T12 and Rent Comps are the **same number to the dollar** ($1,595) — both are HelloData T90 executed asking. The Supply Chart's $1,588 is **−$7 (−0.4%)** because it averages HelloData over the **trailing 12 months** (Q3'25–Q2'26) rather than the trailing 90 days (Apr 14–Jul 13). **Benign — pure averaging-window difference**, not a data conflict. Effective rent lines up the same way: RR-T12 $1,501 vs Rent Comps $1,502 ($1 rounding); Supply Chart Y0 effective ~$1,545 is higher, again a TTM-window / concession-treatment difference, not a conflict.

### 2.2 Occupancy — the four figures are measuring different things; they reconcile once you separate them
| Source | Figure | What it measures |
|---|---:|---|
| RR-T12 (rent roll / T12) | **93.75%** | subject **physical** occupancy, 225/15 of 240, as-of 6/16/26 |
| Supply Chart — subject Y0 | **~93.6%** | subject occupancy from the **financials/T12** |
| Rent Comps — subject | **91.25%** | **CoStar** vendor occupancy |
| Rent Comps — subject | **88.5%** (SUMMARY "89%") | **HelloData leased %** |

**Verdict: all benign, and they order exactly as expected.** The two figures drawn from the subject's **own operating data** — RR-T12's 93.75% and the Supply Chart's 93.6% — **agree** (both are physical/economic occupancy off the rent roll/T12). The lower figures are **vendor / leased measures**: CoStar 91.25% carries the usual vendor lag/definition gap, and HelloData "leased %" (88.5%) is a distinct leased-not-occupied metric. **Underwriting should use 93.75%** (subject physical) as the in-place assumption. The Rent Comps occupancy comparison (subject 91.2%/88.5% vs comp-set 94.2%/92%) is **internally consistent** because it compares CoStar-to-CoStar and HD-to-HD across subject and comps — so the "~3 pts soft vs the stabilized set" read is a valid *relative* signal (supports the mark-to-market/occupancy-firming thesis), even though the subject's absolute in-place occupancy for the model is 93.75%, not 91.2%.

### 2.3 Unit count & mix — TIES ✓
240 units and the **84 / 132 / 24** (1BR/2BR/3BR) split are **identical everywhere**: README snapshot, RR-T12 unit mix (42+42 / 84+48 / 24), Rent Comps subject row (N=84 / Q=132 / T=24), Supply Chart subject (240), and the rent-comps `config.json` counts `[0,84,132,24]`. No discrepancy.

### 2.4 NOI & taxes — one real correction to carry, plus the reset
- The intake's **OpEx ($1,841,644) carries real-estate taxes at the RedIQ line of $293,799.55** (GL `82100 PROPERTY TAX`, coded `ret`, in OpEx — verified on the RedIQ Categorized tab) **plus insurance $59,440** (`82110`).
- The **Tax analysis shows $293,800 is the 14 apartment parcels only** — it **omits parcel 001** (the 257 S 1100 W commercial pad, $8,666.99). True all-15-parcel in-place tax = **$302,467**. The reconciliation ties to the penny ($302,467 − $8,667 = $293,800).
- **Consequence:** the intake NOI of $3,008,750 **overstates the true in-place NOI by $8,667** → **~$3,000,083**. And on a ~$300k/unit trade, taxes reset to **~$350,000**, i.e. **~$56,200 above the intake-carried $293,800** → **Year-1 reassessed NOI ≈ $2,952,550** (before rent upside).
- The intake's finding that the operator books **taxes+insurance ($353,240) below its NOI line** is confirmed and is the reason the operator's printed NOI ($3,361,990) must be discarded. **The tax and intake workstreams are fully consistent** — the tax analysis simply refines the intake's tax line upward ($293,800 → $302,467 in-place, → ~$350,000 reassessed).

### 2.5 Rent-comp subject-vs-comps vs Supply-chart subject-vs-comps — directionally consistent ✓ (different sets, by design)
Both workstreams say **the subject prices below the competitive central tendency**: Rent Comps ~4% under the curated unit-weighted comp market ($1,595 vs $1,660); Supply Chart below the roster median ($1,588 vs $1,724). The **magnitude differs because the sets differ by design** — Rent Comps is a **curated 10-comp garden Class-B set** (2017–2024 vintage, the defensible mark-to-market benchmark), while the Supply Chart roster is **all 16 new-construction properties in the 5-mi ring** (2022–2026), which includes richer/mid-rise/townhome product (Crestview $2,496, Village Square $2,279, Sanctuary $2,224) that lifts the median to $1,724. **Anchor the mark-to-market on the Rent Comps $1,660, not the supply-chart $1,724** (the latter is a broader relative-value frame, not a M2M number). Where the two sets **share comps, the HelloData rents agree within ~1%** (Ember $1,574 vs $1,569; Northshore $1,650 vs $1,641; Embold $1,744 vs $1,724; The Vue $1,817 vs $1,797; Alvera $1,612 vs $1,627) — the one exception is **Elevate at 620** ($1,640 vs $1,568, ~4.4%), explained by its 45 studios + townhome-style 3BR and the window difference (Elevate is already flagged "read with care" in Rent Comps). All benign.

**Consistency bottom line:** nothing fails to tie. The only *numeric* corrections that must flow into the model are (i) taxes $293,800 → $302,467 in-place / ~$350,000 reassessed, and (ii) Other Income/RUBS underwritten to the T12 not the rent roll (§3). Everything else that "differs" is a methodology/window/measure difference that resolves cleanly.

---

## 3. Prioritized open items (one consolidated list)

### BLOCKING — resolve before the underwriting NOI/rent ramp is finalized
1. **Tax reset (assessor discretion, but must be modeled).** Underwrite **Year-1 taxes to the purchase price**, not the trailing bill: ~$350,000 at a ~$300k/unit / ~$72M basis (scale with the §5 table in the tax memo — every +$25k/unit ≈ +$29k/yr tax). Also (a) add the **$8,667 commercial parcel 001** to in-place ($293,800 → $302,467), and (b) confirm **whether parcel 001 conveys** and how its full-rate (non-exempt) tax is handled. Timing/allocation is at the assessor's discretion — treat any Truth-in-Taxation rate step-down as only a modest partial offset. *(Tax workstream — largest controllable OpEx swing.)*
2. **Other Income / RUBS → underwrite to the T12, not the rent roll.** The ResMan rent roll's *scheduled* other income is **$36k/mo** but the T12 books **$67k/mo**; the gap is RUBS/utility reimbursements (`42160 RUBS` ≈ **$328,579/yr**) that carry $0 scheduled charge and are invisible in the roll. Using the roll would understate EGR/NOI by ~$0.37M/yr. *(RR-T12 flag #3 — material to EGR/NOI.)*
3. **Carry the standardized NOI ($3,008,750), never the operator's $3,361,990.** The −$353,240 delta is taxes+insurance booked below the operator's NOI line. Resolved in the intake, but must survive into the model. *(RR-T12 flag #2.)*
4. **Confirm/curate the rent-comp set before relying on the 4% mark-to-market.** The 10-comp set was built as a **defensible first-pass, auto-selected** from properties present in both HelloData and CoStar — an analyst must sign off. Recommended: **ADD The Yard** (2023, 216u, literally adjacent — dropped only for missing per-BR SF) and **Solhavn** (2024, 352u, usable executed rents) with a fuller CoStar export; consider older-vintage brackets (ICO Mayfield, Viewpointe, Aldara) if a wider band is wanted. The whole rent-upside case leans on this set. *(Rent Comps.)*

### INFORMATIONAL / verify (do not block, but close out)
5. **HelloData bundled-fee gap ($111/mo).** HD T90 asking $1,595 sits $111 above the new-lease base ($1,484); candidate flat fees Internet/Cable $109 + Pest $2 coincide. Shown **GROSS, not netted** (operator is Neighborly, not a known all-in advertiser). **Check the property website** for a currently-listed unit — compare HD asking to base vs "Total Monthly" — before any `--hd-fee-offset`. If HD is bundling, the market-rent signal (and the 4% comp gap) shifts. *(RR-T12 §7 / flag #4.)*
6. **Delinquent Rent HIGH audit exception.** RedIQ codes `41120 DELINQUENT RENT` (−$22,671/yr) as `cl` (collection loss, in EGR); the audit's first-pass `onoe` read would raise NOI ~$22.7k. **The intake's own assessment is that RedIQ's `cl` is conventional/correct** — confirm and move on. *(RR-T12 flag #1.)*
7. **Supply-chart forward pipeline = zero relies on CoStar UC=0 alone.** The RealPage pull was the Grid-Performance shape (no Property Status column), so it **cannot independently flag pipeline** — the zero-supply thesis rests entirely on CoStar. Given how load-bearing "no forward supply" is to the rent-push story, run the opt-in **`--diligence` shadow-supply scan** (rezonings, entitled MF land, announced deals) to confirm before leaning on it. *(Supply chart open items #1–2.)*
8. **Occupancy assumption.** Decide explicitly: UW in-place occupancy = **93.75%** (subject physical). The ~3-pt softness vs the stabilized comp set (CoStar/HD basis) is a **relative** mark-to-market/upside signal, not the in-place input. *(Cross-check §2.2.)*
9. **Wasatch Group 0-concession comps.** Parc on 5th, Rivulet, Embold show **0% concession in HelloData** (effective = asking) and dominate the zero-concession camp; if HD under-captures their concessions, their effective rents/PSF are **overstated** — verify before leaning on the effective-rent gap (subject 6% conc vs comp-set 9%). *(Rent Comps.)*
10. **Two small subject GL/OI items.** `DUES & SUBSCRIPTIONS` = **$111,506/yr** (coded `GA`) is unusually large — eyeball its contents; **Valet Trash Service $14/mo** — confirm it nets vs trash expense or books as Other Income. *(RR-T12 flags #5–6.)*
11. **Supply-chart subject Y0→Y6 rent/occ cells are dormant `IFERROR` links** to the model's `Cash Flow (Annual)` tab (they fall back to the HD Y0 values quoted here). They resolve only when the tabs are dragged into the TMG model — expected, not an error. **Elevate at 620** also carries studios + a townhome-style 3BR (1,654 SF); don't over-weight its 3BR $/SF. *(Supply chart #3 / Rent Comps.)*

---

## 4. Files reviewed
- RR-T12 intake: `/home/user/Kelton/analysis/rr-t12-intake/SUMMARY.md`, `…/The_Kelton__Underwriting_Intake.xlsx` (Dashboard, RedIQ Audit, RedIQ Categorized tabs verified)
- Rent Comps: `/home/user/Kelton/analysis/rent-comps/SUMMARY.md`, `…/The_Kelton__Rent_Comps_High_Level.xlsx`, `…/config.json`
- Supply Chart: `/home/user/Kelton/analysis/supply-chart/SUMMARY.md`, `…/The_Kelton__Supply_Chart.xlsx` (Competitive Analysis, Supply & Absorption tabs verified)
- Tax: `/home/user/Kelton/analysis/tax/Kelton_Tax_Analysis.md`, `…/Kelton_Tax_Parcel_Detail.csv`
- Skills: `.claude/skills/{rr-t12-processor,rent-comps-high-level,supply-chart}/SKILL.md`

*All figures independently re-pulled from the workbooks (openpyxl `data_only=True`) and cross-footed; see `Reconciliation_Checks.csv` for the side-by-side.*
