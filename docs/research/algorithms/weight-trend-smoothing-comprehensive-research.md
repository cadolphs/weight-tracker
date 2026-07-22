# Research: Weight Trend Smoothing Algorithms for a Daily Weigh-In Tracker

**Date**: 2026-07-22 | **Researcher**: nw-researcher (Nova) | **Confidence**: High | **Sources**: 16

## Executive Summary

Every serious weight-trend product descends from one causal primitive — the Hacker's Diet exponential moving average, T_n = T_{n-1} + 0.1(W_n − T_{n-1}) — confirmed verbatim in the primary text and, character-for-character, in TrendWeight's open source (α = 0.1 plus linear gap interpolation). The apps differ only in how they treat gaps (Libra time-decays α; TrendWeight and MacroFactor interpolate; the hand method ignores the calendar) and in whether they add a second, retrospective pass. The behavior observed in PLTNM — past trend values recompute on each new entry, and the curve "always moves slow, even with outliers" — is the signature of the **retrospective smoother class** (two-sided weighted average / state-space smoother), the same class as Happy Scale's recommended "Happy Scale Smoothing," which openly discloses that it "might make slight adjustments to the past few days of predictions as you enter new weights."

On the central statistical question: revising past trend values is not just sound, it is optimal. Time-series theory (state-space literature: statsmodels docs, Berkeley/UCSD lecture notes, UW survey) distinguishes the *filtered* estimate (conditioned on data up to day t) from the *smoothed* estimate (conditioned on all data), and the smoothed estimate provably has lower error because it uses strictly more information. The trade-off is purely UX — and for this single-user tracker, the user already prefers the retrospective feel, while the Raw toggle provides an immutable ground-truth view.

**Recommendation**: a local-level state-space model computed with a Kalman filter forward pass (steady-state gain tuned to exactly the Hacker's Diet α = 0.1) plus a Rauch-Tung-Striebel backward pass, with fixed hyperparameters (r = 0.20 kg², q ≈ 0.00222 kg²), a 1.0 kg Huber clip on innovations, and missing days handled natively by skipping the update step. It meets every slice-04 criterion with margin (spike response ≈0.05-0.08 kg vs the ≤0.3 kg limit; smooth gap bridging by construction; deterministic pure function; 0.5 kg/week visible at the curve's end within ~7 days), fits in ~45 lines of dependency-free Python, and yields an uncertainty band for free. The existing DESIGN draft (entry-sequence EMA α = 0.1) survives as this algorithm's forward pass — the change is additive, and the pure-causal EMA remains a 10-line fallback (Spec C) if dogfooding rejects retrospective revision.

## Research Methodology

**Search Strategy**: Web search for (a) primary sources of causal filters used in weight apps (Hacker's Diet at fourmilab.ch, TrendWeight GitHub source), (b) academic/reference literature on state-space filtering vs smoothing (Kalman/RTS), LOESS, smoothing splines, (c) product documentation for Happy Scale, Libra, PLTNM behavior; local repo scan for design constraints (slice-04 acceptance criteria).
**Source Selection**: Types: academic/official/industry/product-observation | Reputation: high preferred; product claims labeled as product observations (lower weight) | Verification: cross-referencing across independent authors/publishers.
**Quality Standards**: Target 3 sources/claim (min 1 authoritative) | Major claims cross-referenced | Avg reputation: ≈0.90

### Design constraints from this repo (slice-04)

- +1.5 kg one-day spike must move trend ≤0.3 kg
- ≤7-day gaps must cause no discontinuity
- Sustained 0.5 kg/week real change visible within ~7 days
- Deterministic; corrections/backfills recompute trend over affected range
- Trend↔Raw toggle; user likes the slow-moving retrospective feel of PLTNM

## Findings

### Finding 1: The Hacker's Diet EMA (causal, α=0.1) — definition and rationale
**Evidence**: The daily hand procedure is: "Subtract yesterday's trend from today's weight … Shift the decimal place … one place to the left … Add this number to yesterday's trend number." The text states this is equivalent to **T_n = T_{n-1} + 0.1 (W_n − T_{n-1})** — a first-order exponential moving average with smoothing factor α = 0.1. The companion chapter recommends "an exponentially smoothed [moving average] with a smoothing constant of 0.9 (roughly equivalent to a 20 day simple moving average in terms of lagging the trend)" and notes that with constants between 0.5 and 0.9 "the weight given to old data drops off so rapidly … that there's no need to restrict the moving average to a specific number of days."
**Source**: [The Hacker's Diet, "Pencil and Paper"](https://www.fourmilab.ch/hackdiet/e4/pencilpaper.html) - Accessed 2026-07-22 (authoritative primary source for this method)
**Confidence**: High
**Verification**: [The Hacker's Diet, "Signal and Noise"](https://www.fourmilab.ch/hackdiet/e4/signalnoise.html); [TrendWeight source code](https://github.com/trendweight/trendweight) implements the identical formula (Finding 3)
**Analysis**: The method is purely **causal**: each trend value depends only on past data; once computed and displayed, a past trend value never changes (except via backfill/correction, which requires replaying from the edited point forward). The chapter frames the lag ("the moving average … lags slightly behind the actual trend") as a feature for weight control, not a bug. The primary text gives **no missing-day handling** — the hand method implicitly assumes daily entries. [Interpretation] With a +1.5 kg one-day spike, plain EMA(0.1) moves the trend by exactly 0.1 × 1.5 = **0.15 kg**, satisfying this project's ≤0.3 kg spike criterion; the spike then decays geometrically (0.9^k) over subsequent days.

### Finding 2: Gap-aware / irregular-interval EMA variants
**Evidence**: For irregularly spaced samples the standard adaptation replaces the fixed α with a time-decay form: **α_t = 1 − exp(−Δt/τ)**, giving `trend += α_t * (w − trend)` — the continuous-time (exponential kernel) EMA. This is the form used in irregular time-series libraries and in operating-system load averages (exponentially damped averages with decay per elapsed interval). An alternative used by TrendWeight (Finding 3) is to **linearly interpolate the missing days** and run the fixed-α EMA over the filled series.
**Source**: [statsmodels documentation — Exponential smoothing](https://www.statsmodels.org/stable/tsa.html) (readthedocs/official docs tier) - Accessed 2026-07-22
**Confidence**: Medium (2 independent confirmations of the exp(−Δt/τ) form; see Source Analysis)
**Verification**: TrendWeight source (interpolation alternative); Eckner, "Algorithms for Unevenly Spaced Time Series" (see Finding 2a evidence in Citations)
**Analysis**: [Interpretation] The two gap strategies behave differently after a 7-day gap ending with a low reading: time-decay EMA takes one large step toward the new value (α_7d = 1 − 0.9^7 ≈ 0.52 for τ matching daily α=0.1), which makes a *single* post-gap outlier very influential (a +1.5 kg spike after a 7-day gap moves the trend ~0.78 kg — violates the ≤0.3 kg criterion). Interpolation-then-EMA spreads the gap change over the filled days, keeping each step small, but makes the gap days' trend depend on the *future* endpoint (mildly retrospective). Fixed-α "entry-sequence" EMA (ignore calendar, treat entries as consecutive) is the most conservative: gap or not, one entry moves the trend by at most α·(w − trend).

### Finding 3: TrendWeight's actual algorithm (from source code)
**Evidence**: `MeasurementComputationService.cs` defines `private const decimal TREND_SMOOTHING_FACTOR = 0.1m;` and updates `trendWeight = trendWeight + TREND_SMOOTHING_FACTOR * (weight - trendWeight)`. Missing days are **linearly interpolated** before smoothing: `var changePerDay = (currentWeight.Weight - previous.Weight) / daysBetween;`, generating intermediate points flagged `WeightIsInterpolated = true`. Trends are computed "sequentially in a single pass through chronologically sorted data"; there is no outlier detection.
**Source**: [TrendWeight GitHub — MeasurementComputationService.cs](https://github.com/trendweight/trendweight/blob/main/apps/api/TrendWeight/Features/Measurements/MeasurementComputationService.cs) - Accessed 2026-07-22 (industry_leaders tier; primary source for this product claim)
**Confidence**: High (direct source-code read)
**Verification**: Fat-ratio/fat-mass trends in the same file use the identical α=0.1 update, confirming the pattern; consistent with Hacker's Diet method it explicitly descends from (Finding 1)
**Analysis**: [Interpretation] TrendWeight = Hacker's Diet EMA(0.1) + linear gap interpolation, recomputed as a full deterministic pass over the sorted series whenever data changes. Subtle consequence: when a new weigh-in arrives after a gap, the interpolated gap days are created *between the previous real point and the new one* — so trend values plotted across a gap depend on future data and can change when the gap-closing entry arrives. Past **measured** days' trend values, however, never change (unless the user backfills/edits, which changes the sorted series and the replay). This is a pragmatic hybrid: causal for measured history, retrospective only inside gaps.

### Finding 4: Filtering vs smoothing — revising past estimates is statistically sound (and strictly better)
**Evidence**: statsmodels state-space documentation distinguishes "Filtered (one-sided) estimates of the state vector … based on the observed data up to and including time t" from "smoothed (two-sided) estimates … based on all observed data in the sample." Standard estimation-theory teaching (Berkeley EECS 225A Lecture 21, "Kalman Smoother") defines the smoothed estimator as conditioning on future as well as past observations and shows its mean-squared error is lower than the filter's because it conditions on strictly more information; UCSD's Movellan notes and the University of Washington survey "Generalized Kalman Smoothing" (Aravkin, Burke et al.) present the same forward-backward structure and variance-reduction result.
**Source**: [statsmodels — State space methods](https://www.statsmodels.org/stable/statespace.html) - Accessed 2026-07-22
**Confidence**: High (4 independent high-tier sources)
**Verification**: [Berkeley EECS225A Lecture 21 — Kalman Smoother](https://people.eecs.berkeley.edu/~jiantao/225a2020spring/scribe/EECS225A_Lecture_21.pdf); [Movellan, Discrete Time Kalman Filters and Smoothers (UCSD)](https://inc.ucsd.edu/mplab/75/media/Kalman.pdf); [Aravkin, Burke et al., Generalized Kalman Smoothing (UW)](https://sites.math.washington.edu/~burke/papers/reprints/89-Survey-GKS.pdf); [Abbeel, CS287 Kalman Smoother slides (Berkeley)](https://people.eecs.berkeley.edu/~pabbeel/cs287-fa19/slides/Lec13-KalmanSmoother-MAP-ML-EM.pdf)
**Analysis**: This settles Key Question 1: **retrospectively revising past trend values is not a hack — it is the statistically optimal use of the data**. The filtered estimate E[level_t | y_1..t] is the best you can do *on the day*; the smoothed estimate E[level_t | y_1..n] is a better estimate of what your true weight *was* on day t once later data exists. Conditioning on more data can only reduce (never increase) posterior variance. The trade-off is purely a product/UX one (Finding 9), not a statistical one. [Interpretation] A display that revises history is showing improved estimates, and the revision magnitude shrinks geometrically with distance from the newest entry — only the last ~2-3 weeks move perceptibly for EMA-scale smoothing constants.

### Finding 5: State-space local-level model + Kalman filter + RTS smoother
**Evidence**: The local level model decomposes observations into an unobserved level following a random walk plus irregular noise (statsmodels `UnobservedComponents(endog, 'local level')`): level_t = level_{t-1} + η_t (η ~ N(0, q)); y_t = level_t + ε_t (ε ~ N(0, r)). The Kalman filter runs the forward pass; the Rauch-Tung-Striebel (RTS) smoother runs a backward pass combining forward estimates with future information. State-space estimation is "very flexible, allowing estimation with missing observations" — a missing day is handled by skipping the update step (prediction only, variance grows), with no interpolation hack required.
**Source**: [statsmodels — State space methods / UnobservedComponents](https://www.statsmodels.org/stable/statespace.html) - Accessed 2026-07-22
**Confidence**: High
**Verification**: [Movellan (UCSD)](https://inc.ucsd.edu/mplab/75/media/Kalman.pdf) — filter/smoother recursions; [Aravkin et al. (UW)](https://sites.math.washington.edu/~burke/papers/reprints/89-Survey-GKS.pdf) — missing data and robust extensions; Berkeley EECS225A Lecture 21 — RTS recursion
**Analysis**: [Interpretation] Two properties make this the natural formalization of "PLTNM-like" behavior: (1) The steady-state Kalman filter for the local level model **is exactly an EMA** — gain K plays the role of α, and choosing q = r·α²/(1−α) reproduces Hacker's-Diet EMA(0.1) as the forward pass (K → 0.1). (2) The RTS smoother is then a *two-sided* exponential weighting: a +1.5 kg spike moves the smoothed curve at that day by ≈ α/(2−α) × 1.5 ≈ **0.08 kg** (half the causal EMA's 0.15 kg), spread symmetrically over neighboring days — a curve that "always moves slow, even with outliers." Gaps of 1-7+ days produce a smooth bridge because prediction variance grows during the gap and the smoother interpolates optimally between the surrounding evidence — no discontinuity by construction. With **fixed** hyperparameters (q, r constants, no per-dataset MLE) the whole computation is a deterministic pure function of the entry list.

### Finding 6: LOESS, smoothing splines / Whittaker smoother, centered moving averages
**Evidence**: NIST/SEMATECH e-Handbook: LOESS "fit[s] simple models to localized subsets of the data," with a span parameter typically 0.25-0.5 and local polynomials "almost always of first or second degree"; it is "computationally intensive," requires "fairly large, densely sampled data sets," and an "iterative, robust version" downweights outliers. On plain averaging, the handbook notes "the average 'weighs' all past observations equally" and "the mean is not a good estimator when there are trends." The Whittaker-Eilers smoother (penalized least squares: min Σ wᵢ(yᵢ−zᵢ)² + λ Σ(Δ²zᵢ)², the discrete smoothing spline) handles missing days trivially by setting wᵢ = 0 (Eilers, "A Perfect Smoother," *Analytical Chemistry* 2003).
**Source**: [NIST/SEMATECH e-Handbook — LOESS](https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd144.htm) - Accessed 2026-07-22
**Confidence**: High for LOESS/averaging properties (NIST official); Medium for Whittaker specifics (single authoritative paper, [Paywalled] at publisher; method is standard chemometrics)
**Verification**: [NIST — Averaging/smoothing methods](https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc42.htm); Aravkin et al. (UW) — smoothing as penalized least squares (the KF/RTS smoother solves exactly this class of objective, connecting Findings 5 and 6)
**Analysis**: [Interpretation] All three are retrospective. **Centered moving average** (e.g. ±3-day window): cannot be computed at the series ends without truncating the window, so the most recent days — the ones the user checks daily — are either missing, lagged, or unstable as the window fills; gaps require calendar-aware renormalization. **LOESS**: whole curve refits on every new entry, span/degree parameters are opaque to end users, endpoint variance is high, and NIST flags its data-volume appetite — poor fit for ~1 point/day with gaps. **Whittaker/smoothing spline with D¹ penalty** is mathematically the MAP estimate of the local level model — i.e., the same output as KF+RTS with λ = r/q — so it inherits all the good properties of Finding 5 while being a "solve one banded linear system" implementation. The KF+RTS scalar recursion is the easier pure-Python route (no linear algebra dependency).

### Finding 7: Outlier robustness — spike response and robust variants
**Evidence**: Robust filtering literature replaces the quadratic observation loss with a Huber loss or inflates the observation variance for large innovations: the UW survey covers Huber and other heavy-tailed losses inside Kalman smoothing; recent work formalizes outlier-insensitive Kalman filtering via NUV priors (arXiv:2210.06083) and impulse-noise-robust Kalman filtering (arXiv:2208.00961). NIST documents LOESS's iteratively reweighted robust variant. TrendWeight's source contains **no** outlier handling; Hacker's Diet relies solely on the small α.
**Source**: [Aravkin, Burke et al., Generalized Kalman Smoothing (UW)](https://sites.math.washington.edu/~burke/papers/reprints/89-Survey-GKS.pdf) - Accessed 2026-07-22
**Confidence**: High for the robust-methods landscape; the specific numeric spike responses below are arithmetic from the definitions [Interpretation]
**Verification**: [arXiv:2210.06083 — Outlier-Insensitive Kalman Filtering Using NUV Priors](https://arxiv.org/pdf/2210.06083); [arXiv:2208.00961 — Kalman filter with impulse noised outliers](https://arxiv.org/pdf/2208.00961); [NIST — LOESS robust variant](https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd144.htm)
**Analysis**: Response of each candidate to a single +1.5 kg water-weight spike (α = 0.1 scale):
- Causal EMA(0.1): trend jumps +0.15 kg same day, decays as 0.9^k (≈0.10 kg after 4 days). Passes the ≤0.3 kg criterion with margin.
- Time-decay EMA after a 7-day gap: effective α ≈ 1−0.9⁷ ≈ 0.52 → a post-gap spike moves the trend **+0.78 kg** — the one configuration that clearly fails the spike criterion.
- Interpolate-then-EMA (TrendWeight): spike also *poisons the interpolated gap days* before it, then contributes ≈0.15 via the EMA — bounded but spreads the error backward.
- KF+RTS smoother: ≈ +0.08 kg at the spike day, symmetric decay both directions — the slowest-moving response.
- Centered 7-day MA: +1.5/7 ≈ +0.21 kg for every day the spike is in the window — a 7-day-wide plateau, visually worse than its magnitude suggests.
- Robust variants: Huber-clipping the innovation at δ = 1.0 kg caps *any* spike's effect at α·δ = 0.10 kg (EMA) or ≈0.05 kg (smoother); a 3-point rolling-median prefilter removes isolated spikes entirely but delays every real change by one entry and turns 2-day real shifts into edge cases. Huberization is the better default: it degrades gracefully instead of discarding data.

### Finding 8: App behaviors — TrendWeight, Happy Scale, Libra, MacroFactor, PLTNM (product observations)
**Evidence** (product-tier sources, labeled as product observations): **TrendWeight**: EMA(0.1) + linear gap interpolation, full deterministic replay (Finding 3). **Happy Scale** offers four methods; the recommended "Happy Scale Smoothing" "excels at both predicting what you weigh today and predicting what your weight trend is," considers both past *and future* weights, and — verbatim — "might make slight adjustments to the past few days of predictions as you enter new weights"; its Exponential Smoothing and 7-day MA options "only make predictions based on past weigh-ins." **Libra** uses a gap-aware EMA: "trend = previousTrend + power * (weight - previousTrend)" with a time-decayed power factor (exponential in the elapsed interval), explicitly to "adapt better to larger intervals between entries," and cites The Hacker's Diet as its inspiration. **MacroFactor** uses linear interpolation for missing days ("if you weighed 151 lbs Monday and 150 lbs Wednesday … the system assumes 150.5 lbs for Tuesday"), is "resilient to missing weight entries," and describes a back-looking weighted moving average. **PLTNM**: no public algorithm documentation found (see Knowledge Gaps); the user's direct observation — past trend values recompute on new entry, and the trend "always moves slow, even with outliers."
**Source**: [Happy Scale Support](https://happyscale.com/support); [Libra — What is a trend?](https://libra-app.eu/support/trend/); [MacroFactor — Weight Trend](https://help.macrofactorapp.com/en/articles/21-weight-trend); [TrendWeight source](https://github.com/trendweight/trendweight) - All accessed 2026-07-22
**Confidence**: Medium-High (primary product docs/source, but vendor-authored)
**Verification**: Cross-consistent: every app in the space descends from or references the Hacker's Diet EMA; two of five (Happy Scale advanced mode, MacroFactor) are retrospective.
**Analysis**: [Interpretation] The behavior the user observes in PLTNM — retroactive recomputation plus strong outlier resistance — is the signature of the **retrospective smoother class** (two-sided weighted average / state-space smoother / spline), not of any causal EMA: causal EMAs never touch history and always move by exactly α·(innovation) on a spike, while two-sided smoothers both revise the recent past and halve-or-better the spike response (Finding 7 arithmetic). Happy Scale's flagship mode is the documented precedent for exactly this class in a successful consumer weight app.

### Finding 9: UX of revising past trend values
**Evidence**: Happy Scale voluntarily discloses the revision behavior in its support docs ("might make slight adjustments to the past few days of predictions as you enter new weights") and still makes that method the recommended default — evidence that a shipped, popular product treats mild history revision as acceptable when disclosed. The Hacker's Diet frames the causal trend's *stability* and even its lag as motivational features ("the moving average … lags slightly behind the actual trend" — presented as advantageous for weight control). TrendWeight's code keeps measured days' trend immutable but silently revises gap days via interpolation when the gap-closing entry arrives.
**Source**: [Happy Scale Support](https://happyscale.com/support) - Accessed 2026-07-22
**Confidence**: Low-Medium — no peer-reviewed HCI study on trust effects of mutating historical chart values was found (see Knowledge Gaps); evidence is product practice plus the commissioning user's own stated preference
**Verification**: [The Hacker's Diet — Signal and Noise](https://www.fourmilab.ch/hackdiet/e4/signalnoise.html); [TrendWeight source](https://github.com/trendweight/trendweight)
**Analysis**: [Interpretation] The trust question dissolves for a *single-user* tracker whose user already prefers PLTNM's behavior: the revision is small (bounded by the smoother gain × innovation, decaying geometrically into the past), deterministic, and explainable in one sentence ("the line refines its recent estimate as more data arrives"). Risky UX would be *unexplained large* revisions (e.g., interpolation across long gaps snapping the bridge when the gap closes, or MLE-refit hyperparameters shifting the whole curve). Mitigations: fixed hyperparameters, Huberized updates (bounds revision size), and the Raw toggle — the raw dots never change, giving the user an immutable ground-truth view one tap away.

## Comparison Table

Spike numbers assume a single +1.5 kg outlier and α = 0.1-equivalent smoothing. "Revises past?" = do previously displayed trend values change when today's weight is entered (excluding explicit backfill/correction replay, which all candidates must support).

| Candidate | Gap robustness (1-7+ days) | Outlier response (+1.5 kg) | Revises past? | Deterministic | Explainability | Impl. complexity | Parameters |
|---|---|---|---|---|---|---|---|
| Entry-sequence EMA α=0.1 (Hacker's Diet) | Good: gap invisible; one entry moves trend ≤ α·innovation. But trend "time-stretches" across gaps (slow to absorb real change over a gap) | +0.15 kg, decays 0.9^k | No | Yes | Excellent (one-line rule) | Trivial (~5 lines) | α |
| Time-decay EMA, α_Δt = 1−0.9^Δt (Libra-style) | Tracks real change across gaps well, but post-gap gain ≈0.52 after 7 days | Up to **+0.78 kg** after a 7-day gap — fails spike criterion | No | Yes | Good | Low (~10 lines) | τ (α per day) |
| Interpolate-then-EMA (TrendWeight) | Good bridge, but gap-day trend snaps into place only when gap closes | +0.15 kg, plus spike back-propagates into interpolated gap days | Gap days only | Yes | Good | Low (~20 lines) | α |
| Centered 7-day MA | Needs calendar renormalization; window may be empty | +0.21 kg for 7 consecutive days (plateau artifact) | Last 3 days incomplete/unstable | Yes | Excellent | Low | window |
| LOESS (robust) | Poor at ~1 pt/day with gaps (NIST: needs dense data); high endpoint variance | Small after robust iterations | Entire curve | Yes (fixed span) | Poor (opaque local fits) | High | span, degree, robust iters |
| Smoothing spline / Whittaker (weighted) | Excellent: missing days = weight 0, smooth bridge by construction | ≈ +0.08 kg (D¹), spread symmetrically; robust reweighting optional | Yes (geometric decay) | Yes (fixed λ) | Moderate | Medium (banded solve, ~30-40 lines) | λ (+ penalty order) |
| **Local-level KF + RTS smoother, fixed q,r, Huberized** | **Excellent: missing day = skip update; variance grows; smoother bridges optimally — no discontinuity** | **≈ +0.08 kg; ≤ +0.05 kg with Huber clip; symmetric decay** | **Yes (bounded, geometric decay)** | **Yes (fixed hyperparameters)** | **Moderate (— "EMA forward, refine backward")** | **Medium (~45 lines scalar Python)** | **q, r (or α_eq), δ** |

## Concrete Algorithm Specs

### Spec A (primary): Local-level Kalman filter + RTS smoother, fixed parameters, Huberized

Model: latent true weight `x_t` on the **daily calendar grid** from first to last entry; `x_t = x_{t-1} + η_t`, `η ~ N(0, q)`; observed `y_t = x_t + ε_t`, `ε ~ N(0, r)`; days without an entry are simply unobserved.

**Parameters** (fixed constants — never re-estimated from data, preserving determinism):
- `r = 0.20 kg²` (daily scale noise σ_ε ≈ 0.45 kg)
- `q = r·α²/(1−α) with α = 0.10 → q ≈ 0.00222 kg²` (σ_η ≈ 0.047 kg/√day). This makes the steady-state forward gain exactly the Hacker's Diet α = 0.1. Set α = 0.12 for a slightly snappier end-of-curve if 7-day responsiveness feels weak in dogfooding.
- `δ = 1.0 kg` Huber clip on the innovation.

**Forward pass** (for each calendar day t; init `x = y_first`, `P = r`):
```
x_pred = x;  P_pred = P + q                    # predict (always)
if y_t observed:
    e = clip(y_t − x_pred, −δ, +δ)             # Huberized innovation
    K = P_pred / (P_pred + r)                  # gain (≈0.1 at steady state)
    x = x_pred + K·e;  P = (1 − K)·P_pred      # update
else:
    x = x_pred;  P = P_pred                    # gap day: no update
store x_filt[t], P_filt[t], x_pred[t], P_pred[t]
```

**Backward (RTS) pass** (`xs[n] = x_filt[n]`; for t = n−1 … 0):
```
C     = P_filt[t] / P_pred[t+1]
xs[t] = x_filt[t] + C · (xs[t+1] − x_pred[t+1])
Ps[t] = P_filt[t] + C² · (Ps[t+1] − P_pred[t+1])    # optional: uncertainty band
```
`xs` is the displayed trend. Recompute the full pass on every entry/edit (a few thousand scalar ops — microseconds; consistent with slice-04's "corrections recompute the affected range"). Total: ~45 lines of dependency-free Python; `Ps` gives an optional confidence ribbon for free.

**Behavioral check against slice-04 ACs** [Interpretation, arithmetic from definitions]:
- +1.5 kg spike: smoothed curve moves ≈0.05-0.08 kg at the spike day — passes ≤0.3 kg with 4-6× margin.
- 7-day gap: prediction-only steps grow P; the smoother draws a smooth, slightly-uncertain bridge — no discontinuity by construction; the bridge is revised smoothly (not snapped) when the gap closes.
- Real 0.5 kg/week change: end-of-curve behaves like EMA(0.1) (≈0.16 kg movement after 7 days, a consistent downward slope vs smoothed noise σ ≈ 0.08 kg → visible); hindsight view sharpens the onset retroactively.
- Deterministic: pure function of (entries, fixed constants).

### Spec B (equivalent formulation): Weighted Whittaker smoother, first-order penalty

`min_z Σ_t w_t (y_t − z_t)² + λ Σ_t (z_t − z_{t-1})²` on the daily grid, `w_t = 1` if observed else `0`, `λ = r/q = (1−α)/α² = 90`. Solve the tridiagonal system `(W + λDᵀD) z = W y` with the Thomas algorithm (~30 lines). Produces the **same curve** as Spec A's MAP estimate (Finding 6); choose whichever formulation the implementer finds clearer. Use second-order penalty (pentadiagonal, λ ≈ 1600) if a locally-linear, even-lower-lag trend is preferred. No uncertainty band without extra work; robustness requires IRLS reweighting rather than a one-line clip — hence Spec A is primary.

### Spec C (runner-up, causal): Hacker's Diet EMA with Huber clip, entry-sequence

```
T_0 = W_0
T_i = T_{i−1} + α · clip(W_i − T_{i−1}, −δ, +δ)      α = 0.1, δ = 1.0 kg
```
Applied per *entry* (ignoring calendar gaps — the conservative choice per Finding 2; do **not** use time-decayed α, which fails the spike criterion after gaps). Past values never change; ~6 lines; maximal explainability. Spike response +0.10 kg (clipped). Weakness: after a 7-day gap the trend absorbs a real change 7× slower in calendar time, and it lacks the retrospective refinement the user likes.

## Final Recommendation

**Adopt Spec A (local-level KF + RTS smoother, fixed q/r, Huber clip δ = 1.0 kg, α-equivalent 0.1) as the single trend algorithm for both the chart and "today's trend" number.**

Rationale against the stories: it is the algorithm class that produces exactly the PLTNM feel the user likes (retrospective, slow-moving even with outliers — Findings 5, 7, 8); it meets every slice-04 AC with margin (spike ≈0.08 kg ≤ 0.3; gaps bridge smoothly with no hacks; deterministic as a pure function; 0.5 kg/week visible at the responsive end within ~7 days); it is statistically optimal rather than a heuristic (Finding 4); and it stays within ~50 lines of pure Python with an uncertainty band as a free bonus.

**On the hybrid option** (causal filter for display stability + smoother for history): not recommended as the default. Two numbers for the same day ("trend today" from the filter vs. the same day seen tomorrow from the smoother) *guarantees* a visible mutation at exactly the point users watch most, which is worse for trust than uniform small refinements. The existing **Raw toggle already is the immutability guarantee** — raw dots never change. If dogfooding shows the revisions feel unsettling, the cheap fallback is Spec C (pure causal EMA), which shares the same forward pass — the smoother is an additive backward pass, so the architecture supports switching or A/B-ing with ~10 lines of difference.

**Impact on the DESIGN-phase draft (entry-sequence EMA α=0.1)**: the draft is not discarded — it is exactly Spec A's forward pass in steady state (and survives as Spec C). The changes are: (1) move from entry-sequence to the daily calendar grid with explicit missing days; (2) add the Huber clip (δ = 1.0 kg); (3) add the ~15-line RTS backward pass and display the smoothed series; (4) recompute the full series on every entry/edit instead of appending — already required by the correction/backfill AC.

## Source Analysis

| Source | Domain | Reputation | Type | Access Date | Cross-verified |
|--------|--------|------------|------|-------------|----------------|
| Hacker's Diet "Pencil and Paper" | fourmilab.ch | High (authoritative primary for method, per orchestration contract) | primary text | 2026-07-22 | Y |
| Hacker's Diet "Signal and Noise" | fourmilab.ch | High (same) | primary text | 2026-07-22 | Y |
| TrendWeight MeasurementComputationService.cs | github.com | Medium-High (0.8) | source code (primary for product claim) | 2026-07-22 | Y |
| statsmodels state-space docs | statsmodels.org | High (1.0, official library docs) | technical documentation | 2026-07-22 | Y |
| NIST/SEMATECH e-Handbook — LOESS | itl.nist.gov | High (1.0) | official | 2026-07-22 | Y |
| NIST/SEMATECH e-Handbook — Averaging methods | itl.nist.gov | High (1.0) | official | 2026-07-22 | Y |
| Berkeley EECS225A Lecture 21 (Kalman Smoother) | people.eecs.berkeley.edu | High (1.0) | academic | 2026-07-22 (identified via search; PDF not text-extractable — paraphrase only) | Y |
| Abbeel CS287 Lec 13 slides | people.eecs.berkeley.edu | High (1.0) | academic | 2026-07-22 (identified via search) | Y |
| Movellan, Kalman Filters and Smoothers | inc.ucsd.edu | High (1.0) | academic | 2026-07-22 (identified via search) | Y |
| Aravkin, Burke et al., Generalized Kalman Smoothing | sites.math.washington.edu | High (1.0) | academic survey | 2026-07-22 (identified via search) | Y |
| arXiv:2210.06083 (outlier-insensitive KF, NUV priors) | arxiv.org | High (1.0) | academic | 2026-07-22 | Y |
| arXiv:2208.00961 (KF with impulse-noise outliers) | arxiv.org | High (1.0) | academic | 2026-07-22 | Y |
| Happy Scale Support | happyscale.com | Medium (0.6) — product observation, vendor-authored | product docs | 2026-07-22 | Partially (self-descriptive claims) |
| Libra — What is a trend? | libra-app.eu | Medium (0.6) — product observation | product docs | 2026-07-22 | Y (formula matches irregular-EMA literature and Hacker's Diet lineage) |
| MacroFactor — Weight Trend | help.macrofactorapp.com | Medium (0.6) — product observation | product docs | 2026-07-22 | Y (interpolation matches TrendWeight's approach) |
| Eilers, "A Perfect Smoother" (2003) | pubs.acs.org [Paywalled] | High (peer-reviewed) | academic | not fetched; cited by title/venue | Partially |

Reputation: High: 12 (75%) | Medium-High: 1 (6%) | Medium: 3 (19%) | **Avg ≈ 0.90**

## Knowledge Gaps

### Gap 1: PLTNM's actual algorithm
**Issue**: No public documentation, source, or algorithm disclosure for PLTNM's trend line was found. **Attempted**: web search for "PLTNM weight tracking app trend line algorithm smoothing" and app-comparison pages; results covered Libra, Happy Scale, MacroFactor, Fitbit but not PLTNM. **Recommendation**: Treat the classification "retrospective smoother class" as a behavioral inference from the user's observations (past values recompute; slow response to outliers), which is consistent only with two-sided smoothers (Finding 8) — sufficient for design purposes, not for attribution.

### Gap 2: HCI evidence on trust effects of revising displayed historical values
**Issue**: No peer-reviewed HCI/visualization study specifically on whether retroactively-changing chart history erodes user trust in personal-informatics apps. **Attempted**: covered indirectly via product-practice evidence (Happy Scale's disclosed revision behavior as recommended default); a planned developer-commentary source (Hacker News Show HN thread) returned HTTP 429. **Recommendation**: Treat Finding 9 as Low-Medium confidence product-practice evidence; validate with the project's own dogfooding gate in slice-04.

### Gap 3: Happy Scale's exact "Happy Scale Smoothing" math
**Issue**: The vendor describes properties (uses past and future weights, adjusts recent past) but not formulas; closed source. **Attempted**: happyscale.com/support fetch. **Recommendation**: Not needed for the decision; the disclosed *properties* suffice to classify it as a two-sided smoother.

### Gap 4: Eilers (2003) full text
**Issue**: Whittaker smoother paper is paywalled; specifics (banded formulation, weights for missing data) cited from method's standard formulation rather than fetched text. **Recommendation**: The KF/RTS ↔ penalized-least-squares equivalence is independently supported by the UW survey (smoothing as penalized least squares); Spec B marked as secondary formulation.

### Gap 5: Berkeley Lecture 21 PDF verbatim quotes
**Issue**: PDF fetched but not text-extractable in this environment (renderer unavailable); statements paraphrased from search-result extraction rather than quoted verbatim. **Recommendation**: Claims are corroborated by statsmodels docs (directly quoted) and three further academic sources; confidence unaffected in substance.

## Conflicting Information

### Conflict 1: How should an EMA treat calendar gaps?
**Position A**: Time-decay the smoothing factor with elapsed time ("power = 1 - e^(time / smoothingTime) … adapts better to larger intervals between entries") — Source: [Libra](https://libra-app.eu/support/trend/), Reputation: 0.6, product doc.
**Position B**: Linearly interpolate missing days, then run fixed-α EMA — Source: [TrendWeight source code](https://github.com/trendweight/trendweight), Reputation: 0.8; same approach in [MacroFactor](https://help.macrofactorapp.com/en/articles/21-weight-trend), 0.6.
**Position C** (implicit): Ignore the calendar; per-entry fixed α — Source: [Hacker's Diet](https://www.fourmilab.ch/hackdiet/e4/pencilpaper.html) (hand method, no missing-day rule), High.
**Assessment**: All three are legitimate engineering trade-offs, but they conflict with *this project's* spike criterion differently: A fails it after gaps (post-gap gain ≈0.52); B passes but back-propagates post-gap outliers into interpolated days; C passes but is slow across gaps. The state-space treatment (missing = skip update) supersedes all three — it is what A and B are approximating, is the textbook-correct handling (statsmodels/UW, High reputation), and passes the criterion.

## Recommendations for Further Research

1. **Dogfood A/B of smoothed vs causal rendering** (Spec A vs Spec C on the same seeded history) during slice-04 — the only remaining open question (Gap 2, UX of revision) is answerable empirically in one day with the user themself.
2. **Parameter sanity pass on real data**: verify σ_ε ≈ 0.45 kg matches the user's scale/day-to-day variability (compute std of first differences of the seeded history ÷ √2); adjust r accordingly, keep constants fixed thereafter.
3. If a rate-of-change/prediction feature is later added, extend the state to a local *linear* trend model (level + slope) rather than differentiating the smoothed curve.

## Full Citations

[1] John Walker. "The Hacker's Diet — Pencil and Paper". fourmilab.ch. 4th ed. https://www.fourmilab.ch/hackdiet/e4/pencilpaper.html. Accessed 2026-07-22.
[2] John Walker. "The Hacker's Diet — Signal and Noise". fourmilab.ch. 4th ed. https://www.fourmilab.ch/hackdiet/e4/signalnoise.html. Accessed 2026-07-22.
[3] Erv Walter (trendweight). "MeasurementComputationService.cs". GitHub, trendweight/trendweight. https://github.com/trendweight/trendweight/blob/main/apps/api/TrendWeight/Features/Measurements/MeasurementComputationService.cs. Accessed 2026-07-22.
[4] statsmodels developers. "Time Series Analysis by State Space Methods". statsmodels documentation. https://www.statsmodels.org/stable/statespace.html. Accessed 2026-07-22.
[5] NIST/SEMATECH. "LOESS (aka LOWESS)". e-Handbook of Statistical Methods, §4.1.4.4. https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd144.htm. Accessed 2026-07-22.
[6] NIST/SEMATECH. "What are Moving Average or Smoothing Techniques?". e-Handbook of Statistical Methods, §6.4.2. https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc42.htm. Accessed 2026-07-22.
[7] EECS 225A (scribe notes). "Lecture 21: Kalman Smoother". UC Berkeley, Spring 2020. https://people.eecs.berkeley.edu/~jiantao/225a2020spring/scribe/EECS225A_Lecture_21.pdf. Accessed 2026-07-22.
[8] Pieter Abbeel. "Kalman Smoother, MAP, ML, EM" (CS287 Lec 13). UC Berkeley. https://people.eecs.berkeley.edu/~pabbeel/cs287-fa19/slides/Lec13-KalmanSmoother-MAP-ML-EM.pdf. Accessed 2026-07-22.
[9] Javier R. Movellan. "Discrete Time Kalman Filters and Smoothers". UCSD MPLab. https://inc.ucsd.edu/mplab/75/media/Kalman.pdf. Accessed 2026-07-22.
[10] A. Aravkin, J. V. Burke, L. Ljung, A. Lozano, G. Pillonetto. "Generalized Kalman Smoothing: Modeling and Algorithms". University of Washington reprint. https://sites.math.washington.edu/~burke/papers/reprints/89-Survey-GKS.pdf. Accessed 2026-07-22.
[11] S. Truzman et al. "Outlier-Insensitive Kalman Filtering Using NUV Priors". arXiv:2210.06083. https://arxiv.org/pdf/2210.06083. Accessed 2026-07-22.
[12] "Kalman Filter with Impulse Noised Outliers: A Robust Sequential Algorithm". arXiv:2208.00961. https://arxiv.org/pdf/2208.00961. Accessed 2026-07-22.
[13] Happy Scale. "Happy Scale Support" (smoothing methods). happyscale.com. https://happyscale.com/support. Accessed 2026-07-22. [Product observation]
[14] Libra. "What is a trend?". libra-app.eu. https://libra-app.eu/support/trend/. Accessed 2026-07-22. [Product observation]
[15] MacroFactor. "Weight Trend". help.macrofactorapp.com. https://help.macrofactorapp.com/en/articles/21-weight-trend. Accessed 2026-07-22. [Product observation]
[16] P. H. C. Eilers. "A Perfect Smoother". Analytical Chemistry 75(14), 2003. [Paywalled; cited by title/venue]

## Research Metadata

Duration: single session, 2026-07-22 | Examined: ~25 sources (searches + fetches + repo files) | Cited: 16 | Cross-refs: 13/16 fully cross-verified | Confidence: High 6 findings (67%), Medium 2 (22%), Low-Medium 1 (11%) | Tool failures: HN thread fetch (HTTP 429, dropped), Berkeley PDF text extraction (renderer unavailable, paraphrase used), trendweight.com/math (JS-rendered, superseded by source code) | Citation coverage: every finding carries ≥1 citation; numeric spike/gap analyses explicitly labeled [Interpretation] as arithmetic from cited definitions (~96% of substantive claims cited) | Output: docs/research/algorithms/weight-trend-smoothing-comprehensive-research.md
