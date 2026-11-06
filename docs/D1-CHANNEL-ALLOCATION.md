# D1 — Channel allocation: does a bulk ion-channel signature earn its read budget?

**Status:** executed. All figures below were produced by
`relapse-competence allocation` and are committed under `results/`.
**Artefacts:** `results/channel_allocation.json` (50,000×), `results/channel_allocation_200k.json` (200,000×)
**Date:** 2026-11-06
**Question it answers:** the first question of the gap audit's D1 stage — is an
electrical (ion-channel) channel worth the sequencing budget it takes away from
the mutation channel?

---

## A. What D1 is, and what it is not

D1 is a **read-budget decision tool**. It asks: given a fixed number of reads
per draw, how should they be split between

- the **mutation channel** — a tumour-informed panel tracking somatic mutations
  at `n_mutation` loci, which detects *how much tumour is present* and *whether
  it is persisting*, and
- the **bulk electrical channel** — `n_electrical` ion-channel loci read as a
  bulk feature, which carries information about the tumour's *state* (the
  fraction of relapse-competent cells, `f_state`).

**It does not test the biology.** The state fraction is a *modelled parameter*
(`state_fraction_resistant = 0.25`, `state_fraction_persistent = 0.10`), not
something fitted to data. D1 therefore answers "if a channel with this much
information existed, would it be worth building?" — not "does it exist?"

It also does **not** evaluate any wet-lab assay. Nothing here is a clinical
claim.

---

## B. The model changes that made this possible

Three changes to `src/relapse_competence/`, each with its own correctness
guarantee.

### B.1 A third patient arm: `PERSISTENT`

The original model had two post-treatment arms: `RESPONDER` (no residual
disease) and `RESISTANT` (residual clone that regrows and relapses). **That
pair makes MRD look better than it is**, because a positive MRD result can
only come from a patient who either relapses or has no residual disease.

`PERSISTENT` fills the missing cell of the 2×2: residual disease that persists
but does **not** relapse inside the observation window. This is the clinical
population that makes MRD hard, and it is the one that was absent.

### B.2 A latent state, and a bulk channel that carries it

Each patient carries a continuous `state_fraction` — the fraction of their
tumour that is relapse-competent. The state distribution **overlaps heavily**
between relapsers and persistent patients (0.25 ± 0.12 vs 0.10 ± 0.12), so the
electrical channel is informative but far from an oracle.

The bulk channel's per-locus VAF is modelled as

```
VAF_electrical = c · V · shedding · (1 + κ · f_state)      κ = 3.0
```

Note the asymmetry that matters: the marker is present in **all** tumour cells
(the `c · V` term), so its per-locus signal is *not* diluted by clonality the
way a subclonal mutation is. What *is* diluted is the **state**, because only
the `f_state` fraction of cells carries the upregulated channel. That is the
tension the sweep measures.

### B.3 Two scores, because "burden" and "state" are different questions

| Score | Definition | What it measures |
|---|---|---|
| `electrical_raw` | largest electrical read count across draws | a **burden** proxy — the marker scales with tumour volume |
| `electrical_enrichment` | pooled per-locus VAF ratio, electrical ÷ mutation | **state** — the shared burden cancels, leaving only the marker enrichment |

The enrichment ratio is pooled across draws rather than maximised per draw. A
per-draw maximum divides by a possibly tiny mutation read count, so one noisy
early draw produces an arbitrarily large ratio, and taking the maximum then
selects for whoever had the smallest denominator. That bug was found and fixed
during this work; the pooled form has far lower variance.

### B.4 Correctness guarantees

- **The refactor does not change published results.** The `RESPONDER` and
  `RESISTANT` arms draw from the same RNG stream in the same order as before;
  the new arm and the new state parameter use separate derived streams. A
  regression check confirms the original single-channel path still reproduces
  its earlier figures exactly.
- **A physical defect was found and fixed.** The original exponential growth
  model had **no carrying capacity**: a residual clone doubling every 60 days
  reached tens of litres inside a 33-month window, pushing per-locus VAF above
  1 and making the Poisson sampler reject the draw at 200,000× depth. A 5-litre
  carrying capacity and a defensive VAF clamp fix it. This shifted the
  published MRD figures slightly (50,000×/50 loci: sensitivity 0.515 → 0.521,
  median lead 41 d → 39 d); the README table was regenerated from the results
  file, not edited by hand.

---

## C. Results

### C.1 The finding that matters most: MRD specificity is not one number

At 200,000× depth and 200 loci, the same mutation panel gives:

| Specificity measured against | Value |
|---|---:|
| Responders (no residual disease) | **0.983** |
| Persistent patients (MRD-positive, do not relapse) | **0.662** |

And **26% of all MRD-positive patients are persistent non-relapsers.**

**The literature's headline "MRD specificity ≈ 98.5%" is measured against the
easy population.** Against the population that actually causes clinical
false positives, the same assay is at 0.66–0.91 depending on configuration.
Any PPV quoted for an MRD assay without stating which denominator was used is
not interpretable.

### C.2 Does the electrical channel carry state information beyond burden?

Yes. The burden-normalised enrichment score separates relapsers from
non-relapsers **within the MRD-positive population** with AUC **0.85–0.95**
across all configurations — far above the 0.5 null.

The dilution worry that motivated this stage is real but not fatal: the state
signal survives the bulk dilution.

### C.3 But the *practically* better discriminator is the one that is not state-specific

| Score | AUC within MRD+ | What it is |
|---|---:|---|
| `electrical_raw` | **0.993 – 1.000** | burden proxy — "the tumour is regrowing" |
| `electrical_enrichment` | 0.845 – 0.945 | state-specific — the hypothesis under test |

The raw score is the better discriminator, and it is the one that carries *less*
mechanistic information about the relapse-competent state. It works because
relapsing tumours grow and persistent ones do not — which the mutation channel
already partly observes. **A high raw AUC is not evidence for the bioelectric
hypothesis; it is evidence that the tumour is regrowing.**

### C.4 The allocation trade-off (200 loci, 50,000× depth)

| Electrical fraction | n_mut | n_elec | MRD sensitivity | PPV within MRD+ | PPV after refinement | auc_enrichment |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 200 | 0 | **0.834** | 0.734 | 0.734 | 0.500 |
| 0.25 | 150 | 50 | 0.802 (−3.2 pp) | 0.732 | **1.000** | **0.905** |
| 0.50 | 100 | 100 | 0.744 (−9.0 pp) | 0.716 | 1.000 | 0.911 |
| 0.75 | 50 | 150 | 0.598 (−23.6 pp) | 0.699 | 1.000 | 0.912 |
| 1.00 | 0 | 200 | **degenerate** | — | — | — |

**25% is near the knee of the curve.** Going from 0% to 25% costs 3.2 points of
MRD sensitivity and buys the entire PPV gain; going from 25% to 50% costs
another 5.8 points for 0.006 of extra enrichment AUC.

### C.5 The cheaper the mutation panel, the more expensive the electrical channel is

At 50 loci and 50,000× depth:

| Electrical fraction | MRD sensitivity | Cost vs baseline |
|---:|---:|---|
| 0.00 | 0.556 | — |
| 0.25 | 0.434 | **−12.2 pp** |
| 0.50 | 0.254 | −30.2 pp |
| 0.75 | 0.141 | −41.5 pp |

A 50-locus mutation panel cannot afford the electrical channel. The channel
allocation question is therefore **conditional on the mutation panel being
adequately powered** — and 200 loci at 200,000× is the configuration where it
becomes affordable (0.956 → 0.926 sensitivity for a 25% electrical allocation).

### C.6 Depth restores the option

At 200,000× and 200 loci, a 25% electrical allocation costs **3.0 pp** of MRD
sensitivity (0.956 → 0.926) instead of 3.2 pp at 50,000× — but the deeper
configuration starts from a much higher baseline, so the *absolute* cost is
the same while the gain is available at a realistic panel size.

### C.7 100% electrical allocation is degenerate

With no mutation loci there is no MRD assay, so there is nothing for the
electrical channel to refine. The sweep flags these rows explicitly rather
than reporting a meaningless number.

---

## D. Honest limits of this result

1. **The PPV gain is an upper bound.** The model gives `PERSISTENT` patients a
   900-day doubling time (essentially flat) and `RESISTANT` 60 days, so the
   burden proxy separates them almost perfectly and `auc_raw` reaches ~1.0.
   Real persistent-MRD patients regrow slowly; they are not flat. The
   realistic PPV gain will be smaller than 0.73 → 1.00.
2. **The state fractions are assumed.** 0.25 and 0.10 are not fitted to
   anything. The enrichment AUC of 0.85–0.95 is a *conditional* statement:
   *if* the state fraction is separated that way, the channel works.
3. **The refinement operating point is favourable.** The electrical cutoff is
   chosen to retain 90% of relapsing MRD-positive patients. At a stricter
   retention the PPV rises and the sensitivity of the refined call falls.
4. **The model has no noise on the state itself.** Real assays have
   deconvolution error, and the methylation→expression→channel chain adds
   error at every step. None of that is modelled.
5. **One tumour biology, one treatment.** The MRD model has no heterogeneity
   beyond the residual fraction, and no resistant sub-clone dynamics.
6. **The refinement PPV of exactly 1.000 is a model artefact**, not a
   prediction.

---

## E. What this changes in the programme

**The gap is not blocked by the dilution constraint.** The state signal
survives dilution (AUC 0.85–0.95), so D2 — the tissue-level check that the
electrical↔methylation coupling actually transfers to lung — remains worth
doing.

But D1 does change the *shape* of the programme:

- **The first question is no longer "is the electrical state real?"** It is
  **"can it be measured in plasma at a useful operating point?"** — and the
  answer is conditional on a powered mutation panel.
- **The realistic use is not detection, it is refinement.** The mutation
  channel detects; the electrical channel would *stratify* the MRD-positive
  population into "will relapse" and "will not". That is a different, and
  smaller, claim than the one the gap audit implied.
- **The cost is quantified.** The electrical channel is affordable only at
  ≥200 loci with ≥200,000× depth, and only at ≤25% allocation.

**Recommended next step: D2**, the tissue-level check in lung, with a
specific design requirement that D1 adds — the readout must be the
*burden-normalised* enrichment ratio, not the raw marker abundance, because
only the former tests the hypothesis. A tissue study that measured raw
ion-channel abundance would confirm the growth signal and say nothing about
the relapse-competent state.

---

## F. Reproducing this

```bash
relapse-competence allocation --patients 800 --depth 50000  --loci 50,200 \
    --out results/channel_allocation.json
relapse-competence allocation --patients 800 --depth 200000 --loci 50,200 \
    --out results/channel_allocation_200k.json
```

Both files are committed, and `scripts/verify_report_consistency.py` asserts
that the figures quoted in this document match them.
