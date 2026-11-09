# Gate review: the programme's own killing conditions, against measured inputs

**Audit ID:** `gate-review-2026-11`
**Date of run:** 2026-11-09
**Reproduce:** `python scripts/gate_review.py --patients 800`
**Artefacts:** `results/gate_review/gate_review.json`,
`results/gate_review/gate_matrix.tsv`

---

## 1. What this document is

The research plan states five conditions under which the programme is dead
([`RESEARCH-PLAN.md`](RESEARCH-PLAN.md) §0). Until now, two of them had never
been evaluated against anything but the simulator's assumptions. The
state-resolved audits replaced those assumptions with measurements — the
per-cell fold of the state over the surrounding tumour, and the state
fraction — and the window audit produced a verdict per candidate target.

This document applies the plan's own conditions to that evidence and writes the
verdicts down. It is deliberately unflattering in two directions:

- a condition that **cannot be evaluated** is recorded as *not evaluable*,
  never as passed;
- a condition that rests on a **model-based projection** rather than a
  measurement says so, and the projection's inputs are stated.

The headline: **one condition has fired, two cannot yet be tested, and the
surviving readout for each disease is now named.**

## 2. The verdicts

| Condition | What it kills | Status | Fires for |
|---|---|---|---|
| **K1** | The state-specific readout carries no information beyond tumour burden (enrichment AUC ≤ 0.6) | **fired** | every configuration whose channel does not over-express the state — including **NSCLC / PIEZO1** |
| **K2** | The state is not present, or not relapse-associated, in lung (no state-associated methylation delta between primary and relapsed tissue) | **not evaluable** | — |
| **K3** | The state cannot be inferred from plasma at an affordable read budget (enrichment AUC ≤ 0.65 at 200,000× / 200 loci) | **fired** | the same configurations as K1; **none of the three state candidates** |
| **K4** | Every candidate target has an unacceptable therapeutic window | **fired** | — for systemic delivery |
| **K5** | Suppressing the state does not reduce relapse competence in patient-derived models | **not evaluable** | — |

Two of the three K1 firings are the same fact: a channel that does not
over-express the state carries no state information, and no readout can be
built on it. The consequence is not cosmetic.

### The configurations that matter

| Dataset | Channel | Tissue fold | State fraction | Bulk elevation | AUC at 200k× / 200 | K1 | K3 |
|---|---|---:|---:|---:|---:|:--:|:--:|
| NSCLC | **KCNN4** | 3.698 | 0.392 | 2.057 | **0.9929** | pass | pass |
| SCLC | **KCNN4** | 2.554 | 0.104 | 1.162 | 0.7065 | pass | pass |
| SCLC | **PIEZO1** | 3.363 | 0.104 | 1.246 | 0.6945 | pass | pass |
| SCLC | CACNA1E | 1.112 | 0.104 | 1.012 | 0.5727 | **fire** | **fire** |
| NSCLC | PIEZO2 | 1.009 | 0.392 | 1.003 | 0.4930 | **fire** | **fire** |
| NSCLC | PIEZO1 | 0.839 | 0.392 | 0.937 | 0.4658 | **fire** | **fire** |

The three state candidates are the configurations whose channel over-expresses
the state in tissue. **All three survive K1 and K3.** The configurations that
fire are the ones with nothing to measure. The marginal entries (CACNA1E in
SCLC, fold 1.112; PIEZO2 in NSCLC, fold 1.009) are artefacts of a mechanical
threshold — CACNA1E was ruled out as a lung target at D0 regardless.

## 3. What follows

**1. The readout for EGFR-mutant NSCLC is KCa3.1, and PIEZO1 is dead there.**
The NSCLC state does not over-express PIEZO1 (fold 0.839), so the enrichment
AUC is 0.4658 — chance — and both K1 and K3 fire. Had the programme chosen
PIEZO1 as the NSCLC readout on the strength of the SCLC result, **its own kill
conditions would have ended the programme.** The channel that works there is
KCa3.1, at AUC 0.9929.

**2. The relapsed-SCLC readout survives, but only just.** 0.6945 (PIEZO1) and
0.7065 (KCNN4) against K3's 0.65. That margin is thin: the SCLC state
fraction used here is 0.104, pooled over fifteen libraries of seven different
metastatic sites, and a plasma cohort with a lower state fraction would push
the AUC under the threshold. The honest reading is that **the SCLC readout is
not yet established** — it is above the bar on the evidence available, and the
evidence is thin.

**3. K4 has fired, so the systemic drug arm is dead.** No candidate channel has
a bulk-tissue therapeutic window: CACNA1E and STOML3 are not lung targets at
all, and KCNN4, PIEZO1, KCNA3, TMEM150C and PIEZO2 all fail the specificity
verdict. KCa3.1's lung expression is 12× below minor salivary gland, the gene
is loss-of-function intolerant (LOEUF 0.515), and on-target neurological and
cardiac liabilities are recorded; Piezo1 has no separation from PIEZO2 (window
fold 0.851) and no clinical-stage asset.

The state-resolved audits supply the one piece of counter-evidence: the state
itself is channel-high in the target tissue for the matched disease and channel
(NSCLC/KCNN4, 2.97× on detection; SCLC/PIEZO1, 6.91×). So **a state-directed
modality is not excluded by the expression evidence** — but it does not exist,
and nothing in this repository builds one.

**4. Two conditions remain untested, so the programme is not dead.** K2 is the
condition that would say the state is not in lung or not relapse-associated, and
the evidence so far points the other way: in EGFR-mutant NSCLC every
minimal-residual-disease library has a KRT17+ fraction between 0.28 and 0.65,
against a treatment-naive pooled fraction of 0.137. That is not the methylation
delta the condition names, and there is no primary-versus-relapsed methylation
comparison in this repository, so it is recorded as not evaluable rather than
passed. For relapsed SCLC there is no treatment-naive comparator at all. K5
needs a perturbation experiment; the closest available system was the
RORB-loss organoid dataset GSE325242, whose deposit carries no gene annotation
and cannot be measured.

## 4. What would change each verdict

| Condition | What would change it |
|---|---|
| **K1** | A measured plasma cohort in which the matched channel separates relapsers from MRD-positive non-relapsers with an enrichment AUC above 0.6. For NSCLC/KCNN4 the projection is far above the threshold (0.9929) and only a large measurement error would move it; for SCLC/PIEZO1 (0.6945) a modestly lower state fraction would move it under the threshold |
| **K2** | A primary-versus-relapsed tissue comparison showing no state-associated methylation delta, or a treatment-naive SCLC cohort showing the state is already present before therapy |
| **K3** | A plasma cohort in which the matched channel does not clear AUC 0.65 at 200,000× / 200 loci. The projection clears it at every configuration tested, so a real cohort would have to fail the *measurement*, not the model |
| **K4** | A modality that reaches the state selectively: a state-directed conjugate, a tumour-localised agent, or an allele-selective channel modulator. Bulk-tissue specificity alone will not rescue it |
| **K5** | A patient-derived model in which suppressing the state does **not** reduce relapse competence. No such experiment has been run |

## 5. Limitations

- **K1 and K3 are model-based projections, not plasma measurements.** They are
  the simulator run with the measured per-cell fold and the measured state
  fraction, at 800 patients per arm, with thresholds calibrated on a held-out
  split. A real plasma cohort could move them, and the SCLC margins are small
  enough that it could.
- **The verdict uses the plan's own operating point**, not the best
  configuration in the grid. A configuration with a handful of MRD-positive
  patients can produce an AUC of 1.0 by chance; the best-in-grid column is
  reported as context only, and several of its values are artefacts of small
  MRD-positive populations.
- **The SCLC state fraction is pooled** over fifteen libraries of seven
  metastatic sites, because that dataset has no treatment timepoint. The
  NSCLC figure is a per-library median at the residual-disease timepoint.
  They are not the same statistic.
- **"Not evaluable" is not "passed".** Two of the five conditions have not been
  tested, and one of them (K5) cannot be tested with public data at all.
- **The state candidates are mechanical.** A channel counts as a candidate
  when its measured abundance fold exceeds 1; two entries clear that bar by
  less than 12% and one of them was already ruled out at D0.
- **No clinical claim.** Every number is a simulation output informed by public
  measurements, or a measurement on a public deposit.

## 6. Reproducing

```bash
python scripts/gate_review.py --patients 800
```

The run takes about ten minutes: fourteen configurations, each over the
5,000×/50,000×/200,000×/500,000× depth grid at 50 and 200 loci, with the
measured per-cell fold and state fraction injected. The inputs come from
`results/gse299684/state_expression.json`,
`results/gse353299/state_expression.json` and
`results/d0_window_audit/d0_window_audit.json`; the outputs are
`results/gate_review/gate_review.json` and
`results/gate_review/gate_matrix.tsv`, and every number quoted here is checked
against them in CI.
